import os
import pandas as pd
from datetime import date, datetime, timedelta
from supabase import create_client, Client as SupabaseClient
from dotenv import load_dotenv
from typing import Tuple, List, Optional, Dict, Any

load_dotenv()

supabase_url: Optional[str] = os.environ.get("SUPABASE_URL")
supabase_key: Optional[str] = os.environ.get("SUPABASE_KEY")
_supabase_client: Optional[SupabaseClient] = None
_supabase_init_error: Optional[str] = None

try:
    if not supabase_url or not supabase_key:
        _supabase_init_error = "Supabase URL or Key not found in environment variables. Check .env file."
        print(_supabase_init_error)
    else:
        _supabase_client = create_client(supabase_url, supabase_key)
        print("Supabase client initialized successfully in db_utils.")
except Exception as e:
    _supabase_init_error = str(e)
    print(f"Error initializing Supabase client in db_utils: {_supabase_init_error}")
    _supabase_client = None

def get_supabase_client() -> Optional[SupabaseClient]:
    return _supabase_client

def get_supabase_init_error() -> Optional[str]:
    return _supabase_init_error

def fetch_equipments(department_filter: str, search_query: str) -> Tuple[pd.DataFrame, str]:
    client = get_supabase_client()
    empty_df_cols = ['ID', '장비명 (Name)', '부서 (Department)', '총 수량 (Total)', '대여 가능 수량 (Available)']
    empty_df = pd.DataFrame(columns=empty_df_cols)
    if not client:
        return empty_df, get_supabase_init_error() or "Supabase client not initialized."
    try:
        query = client.table("equipments").select("id, name, department, quantity, available_quantity")
        if department_filter and department_filter != "전체":
            query = query.eq("department", department_filter)
        if search_query:
            search_conditions = [f"name.ilike.%{search_query}%"]
            # Basic check if search_query could be an ID
            if search_query.isalnum() and ('-' in search_query or any(char.isdigit() for char in search_query)):
                 search_conditions.append(f"id.eq.{search_query.upper()}")
            query = query.or_(",".join(search_conditions))

        response = query.execute()

        if response.data:
            df = pd.DataFrame(response.data)
            expected_cols_map = {'id':'ID', 'name':'장비명 (Name)', 'department':'부서 (Department)', 'quantity':'총 수량 (Total)', 'available_quantity':'대여 가능 수량 (Available)'}
            df = df.rename(columns=expected_cols_map)
            # Ensure all expected columns exist, adding them with None if missing
            for col_original, col_renamed in expected_cols_map.items():
                if col_renamed not in df.columns and col_original not in df.columns : # if not present with new or old name
                     df[col_renamed] = pd.NA # Use pd.NA for missing data
            df = df[empty_df_cols] # Select and order columns as defined
            return df, "장비 목록을 성공적으로 불러왔습니다."
        else:
            return empty_df, "조건에 맞는 장비가 없습니다."
    except Exception as e:
        error_message = str(e)
        print(f"Error fetching equipments: {e}")
        if "JWT" in error_message or "token" in error_message or "authorization" in error_message.lower():
            return empty_df, f"데이터 조회 중 인증 오류: {error_message}."
        return empty_df, f"장비 목록 조회 중 오류 발생: {error_message}"

def process_rental_request(
    selected_equipment_ids: List[str],
    start_date_str: str,
    end_date_str: str,
    borrower_name: str,
    purpose_text: str,
    user_session: Optional[Any]
) -> Tuple[str, List[str]]:
    client = get_supabase_client()
    if not client:
        return get_supabase_init_error() or "Supabase client not initialized.", selected_equipment_ids
    if not user_session or not hasattr(user_session, 'user') or not user_session.user or not hasattr(user_session.user, 'id'):
        return "오류: 사용자 세션 또는 ID가 없습니다. 다시 로그인 해주세요.", selected_equipment_ids
    if not selected_equipment_ids:
        return "오류: 대여할 장비가 선택되지 않았습니다.", selected_equipment_ids

    user_id = user_session.user.id
    equipment_id_to_rent = selected_equipment_ids[0]

    if not all([start_date_str, end_date_str, borrower_name, purpose_text]):
        return "오류: 모든 필드(시작일, 종료일, 대여자명, 사용 목적)를 입력해야 합니다.", selected_equipment_ids

    try:
        start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError:
        return "오류: 날짜 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력해주세요.", selected_equipment_ids

    if start_date_obj < date.today():
        return "오류: 대여 시작일은 오늘 또는 그 이후여야 합니다.", selected_equipment_ids
    if end_date_obj < start_date_obj:
        return "오류: 대여 종료일은 시작일보다 이후여야 합니다.", selected_equipment_ids

    try:
        eq_response = client.table("equipments").select("name, available_quantity, quantity").eq("id", equipment_id_to_rent).single().execute()
        if not hasattr(eq_response, 'data') or not eq_response.data:
            return f"오류: 장비 ID '{equipment_id_to_rent}' 정보를 찾을 수 없습니다.", selected_equipment_ids

        equipment_name = eq_response.data.get('name', equipment_id_to_rent)
        current_available_quantity = eq_response.data.get('available_quantity')

        if current_available_quantity is None:
             return f"오류: 장비 '{equipment_name}'의 대여 가능 수량 정보를 가져올 수 없습니다.", selected_equipment_ids
        if current_available_quantity < 1:
            return f"오류: 장비 '{equipment_name}'는 현재 대여 가능 수량이 없습니다.", selected_equipment_ids

        conflict_response = client.table("rentals").select("id", count="exact")             .eq("equipment_id", equipment_id_to_rent)             .eq("status", "confirmed")             .lte("start_date", end_date_str)             .gte("end_date", start_date_str)             .execute()

        if conflict_response.count > 0:
            return f"오류: 선택한 장비 '{equipment_name}'는 해당 기간 ({start_date_str} ~ {end_date_str})에 이미 대여 중입니다.", selected_equipment_ids

        rental_data = {
            "equipment_id": equipment_id_to_rent, "start_date": start_date_str, "end_date": end_date_str,
            "borrower_name": borrower_name, "purpose": purpose_text, "user_id": user_id, "status": "confirmed"
        }
        insert_res = client.table("rentals").insert(rental_data).execute()

        if not (hasattr(insert_res, 'data') and insert_res.data and len(insert_res.data) > 0):
            error_detail = "대여 정보 저장 중 알 수 없는 오류."
            if hasattr(insert_res, 'error') and insert_res.error and hasattr(insert_res.error, 'message'):
                 error_detail = insert_res.error.message
            print(f"Rental insert failed: {error_detail} (Response: {insert_res})")
            return f"대여 정보 저장 실패: {error_detail}", selected_equipment_ids

        new_available_quantity = current_available_quantity - 1
        update_eq_res = client.table("equipments").update({"available_quantity": new_available_quantity}).eq("id", equipment_id_to_rent).execute()

        if not (hasattr(update_eq_res, 'data') and update_eq_res.data and len(update_eq_res.data) > 0):
            print(f"Warning: Equip quantity update for {equipment_id_to_rent} failed: {update_eq_res}")
            return f"성공: '{equipment_name}' 대여 완료. 단, 수량 업데이트 실패. 관리자 확인 필요.", []

        return f"성공: 장비 '{equipment_name}' 대여 신청 완료. ({start_date_str} ~ {end_date_str})", []
    except Exception as e:
        print(f"Error processing rental request: {e}, {type(e)}")
        err_msg = str(e)
        if "violates row-level security policy" in err_msg:
            return f"오류: 보안 정책 위반. {err_msg}", selected_equipment_ids
        if "check_constraint" in err_msg and "available_quantity" in err_msg:
            return "오류: DB 제약 조건 위반(수량). 동시 요청일 수 있습니다. 새로고침 후 다시 시도하세요.", selected_equipment_ids
        return f"대여 처리 중 서버 오류: {err_msg}", selected_equipment_ids

def fetch_all_equipments_admin() -> Tuple[pd.DataFrame, str]:
    client = get_supabase_client()
    empty_df_cols = ['ID', '장비명', '부서', '총량', '가용량']
    empty_df = pd.DataFrame(columns=empty_df_cols)
    if not client:
        return empty_df, get_supabase_init_error() or "Supabase client not initialized."
    try:
        response = client.table("equipments").select("id, name, department, quantity, available_quantity").order("id", desc=False).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            expected_cols_map = {'id':'ID', 'name':'장비명', 'department':'부서', 'quantity':'총량', 'available_quantity':'가용량'}
            df = df.rename(columns=expected_cols_map)
            for col_original, col_renamed in expected_cols_map.items():
                 if col_renamed not in df.columns and col_original not in df.columns :
                     df[col_renamed] = pd.NA
            df = df[empty_df_cols]
            return df, "모든 장비 목록을 성공적으로 불러왔습니다."
        else:
            return empty_df, "등록된 장비가 없습니다."
    except Exception as e:
        print(f"Error in fetch_all_equipments_admin: {e}")
        return empty_df, f"관리자 장비 조회 오류: {str(e)}"

def add_equipment_admin(
    eq_id: str, name: str, dept: str, qty_str: str
) -> Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str]]:
    client = get_supabase_client()
    if not client:
        return get_supabase_init_error() or "Supabase client not initialized.", eq_id, name, dept, qty_str

    if not all([eq_id, name, dept, qty_str]):
        return "모든 필드(ID, 이름, 부서, 수량)를 입력해야 합니다.", eq_id, name, dept, qty_str
    try:
        qty = int(qty_str)
    except ValueError:
        return "수량은 숫자여야 합니다.", eq_id, name, dept, qty_str
    if qty <= 0:
        return "수량은 0보다 커야 합니다.", eq_id, name, dept, qty_str

    processed_eq_id = eq_id.strip().upper()
    if not processed_eq_id:
        return "ID는 공백일 수 없습니다.", processed_eq_id, name, dept, qty_str

    try:
        existing_eq = client.table("equipments").select("id", count="exact").eq("id", processed_eq_id).execute()
        if existing_eq.count > 0:
            return f"오류: 장비 ID '{processed_eq_id}'는 이미 존재합니다.", processed_eq_id, name, dept, qty_str

        data = {"id": processed_eq_id, "name": name, "department": dept, "quantity": qty, "available_quantity": qty}
        insert_res = client.table("equipments").insert(data).execute()

        if not (hasattr(insert_res, 'data') and insert_res.data and len(insert_res.data) > 0):
            error_detail = "장비 추가 DB 저장 중 알 수 없는 오류."
            if hasattr(insert_res, 'error') and insert_res.error and hasattr(insert_res.error, 'message'):
                 error_detail = insert_res.error.message
            print(f"Add equipment insert failed: {error_detail} (Response: {insert_res})")
            return f"장비 추가 DB 오류: {error_detail}", processed_eq_id, name, dept, qty_str

        return f"성공: 장비 '{name}' (ID: {processed_eq_id}) 추가 완료.", None, None, None, None
    except Exception as e:
        print(f"Error in add_equipment_admin: {e}")
        return f"장비 추가 처리 중 서버 오류: {str(e)}", processed_eq_id, name, dept, qty_str

def update_equipment_admin(
    original_item_state: Optional[Dict[str, Any]], new_id_str: str, name: str,
    dept: str, new_qty_str: str
) -> Tuple[str, Optional[Dict[str, Any]], Optional[str], Optional[str], Optional[str], Optional[str]]:
    client = get_supabase_client()
    if not client:
        return get_supabase_init_error() or "Supabase client not initialized.", original_item_state, new_id_str, name, dept, new_qty_str

    if not original_item_state or 'ID' not in original_item_state:
        return "수정할 장비를 먼저 목록에서 선택하세요.", original_item_state, new_id_str, name, dept, new_qty_str

    original_id = original_item_state['ID']

    if not all([new_id_str, name, dept, new_qty_str]):
        return "모든 필드(ID, 이름, 부서, 수량)를 입력해야 합니다.", original_item_state, new_id_str, name, dept, new_qty_str

    try:
        new_qty = int(new_qty_str)
    except ValueError:
        return "수량은 숫자여야 합니다.", original_item_state, new_id_str, name, dept, new_qty_str
    if new_qty < 0:
        return "수량은 0 이상이어야 합니다.", original_item_state, new_id_str, name, dept, new_qty_str

    processed_new_id = new_id_str.strip().upper()
    if not processed_new_id:
        return "ID는 공백일 수 없습니다.", original_item_state, processed_new_id, name, dept, new_qty_str

    try:
        current_eq_data_res = client.table("equipments").select("quantity, available_quantity").eq("id", original_id).single().execute()
        if not hasattr(current_eq_data_res, 'data') or not current_eq_data_res.data:
            return f"오류: 원본 장비 ID '{original_id}'를 찾을 수 없습니다.", original_item_state, processed_new_id, name, dept, new_qty_str
        current_eq_data = current_eq_data_res.data

        rented_qty = current_eq_data.get('quantity', 0) - current_eq_data.get('available_quantity', 0)
        new_available_qty = new_qty - rented_qty

        if new_available_qty < 0:
            return f"오류: 새 총 수량({new_qty})은 현재 대여된 수량({rented_qty})보다 적을 수 없습니다. 최소 {rented_qty} 이상이어야 합니다.", original_item_state, processed_new_id, name, dept, new_qty_str

        update_payload: Dict[str, Any] = {
            "name": name, "department": dept, "quantity": new_qty, "available_quantity": new_available_qty
        }

        # Handle ID change. This is complex.
        # If processed_new_id is different from original_id, it means user wants to change the ID.
        if processed_new_id != original_id:
            # Check if new ID already exists
            existing_check = client.table("equipments").select("id", count="exact").eq("id", processed_new_id).execute()
            if existing_check.count > 0:
                return f"오류: 변경하려는 새 ID '{processed_new_id}'가 이미 다른 장비에 사용 중입니다.", original_item_state, processed_new_id, name, dept, new_qty_str

            # IMPORTANT: Directly updating a Primary Key (PK) is often disallowed or problematic.
            # The common way is to INSERT a new record with the new PK and DELETE the old one.
            # This also requires updating all foreign keys in related tables (e.g., 'rentals').
            # This is a very complex operation for this context.
            # For now, we will add the 'id' to the update_payload. If the DB errors because PK cannot be changed,
            # this part of the logic will need significant rework or the feature (changing ID) might be removed.
            update_payload["id"] = processed_new_id
            print(f"Attempting to change equipment ID from {original_id} to {processed_new_id}")


        update_response = client.table("equipments").update(update_payload).eq("id", original_id).execute()

        if not (hasattr(update_response, 'data') and update_response.data and len(update_response.data) > 0):
            error_detail = "장비 정보 업데이트 DB 저장 중 알 수 없는 오류."
            if hasattr(update_response, 'error') and update_response.error and hasattr(update_response.error, 'message'):
                 error_detail = update_response.error.message

            if processed_new_id != original_id and ("primary key" in error_detail.lower() or "constraint" in error_detail.lower()):
                 error_detail = f"장비 ID(PK)는 직접 변경할 수 없습니다. 새 ID로 장비를 추가하고 기존 장비를 삭제하는 방식을 사용해야 합니다. ({error_detail})"
            print(f"Update equipment failed: {error_detail} (Response: {update_response})")
            return f"장비 정보 업데이트 실패: {error_detail}", original_item_state, processed_new_id, name, dept, new_qty_str

        final_id = processed_new_id if processed_new_id != original_id else original_id
        return f"성공: 장비 ID '{original_id}' 정보가 '{final_id}'로 업데이트되었습니다.", None, None, None, None, None
    except Exception as e:
        print(f"Error in update_equipment_admin: {e}, {type(e)}")
        return f"장비 수정 처리 중 서버 오류: {str(e)}", original_item_state, processed_new_id, name, dept, new_qty_str

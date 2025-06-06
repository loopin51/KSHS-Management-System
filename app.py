import os
import gradio as gr
from supabase import create_client, Client
from dotenv import load_dotenv
import re
import pandas as pd
from datetime import date, datetime, timedelta

# Load environment variables from .env file
load_dotenv()

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")

supabase_url: str = os.environ.get("SUPABASE_URL")
supabase_key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = None

try:
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL or Key not found. Check .env file.")
    supabase = create_client(supabase_url, supabase_key)
    print("Supabase client initialized successfully.")
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    supabase = None

# --- Authentication Functions ---
def is_valid_email(email):
    if not email: return False; pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"; return re.match(pattern, email) is not None
def signup_user(email, password, confirm_password):
    if not supabase: return "Supabase client not initialized."
    if not is_valid_email(email): return "Invalid email format."
    if not password: return "Password cannot be empty."
    if password != confirm_password: return "Passwords do not match."
    if len(password) < 6: return "Password must be at least 6 characters long."
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user and res.user.aud == 'authenticated': return f"Signup successful for {email}! Check email to confirm." if not res.session else f"Signup successful! Welcome {res.user.email}."
        elif hasattr(res, 'error') and res.error: return f"Signup failed: {res.error.message}"
        else:
            try:
                if supabase.auth.sign_in_with_password({"email": email, "password": password}).user: return "This email is already registered and confirmed. Please log in."
            except: pass
            return "Signup failed. The email might already be in use or an issue occurred."
    except Exception as e:
        if "User already registered" in str(e) or (hasattr(e, 'message') and "User already exists" in e.message): return "User already registered. Please log in or check email."
        return f"An unexpected error occurred during signup: {str(e)}"
def login_user(email, password):
    if not supabase: return None, "Supabase client not initialized."
    if not is_valid_email(email): return None, "Invalid email format."
    if not password: return None, "Password cannot be empty."
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.user and res.session: print(f"User {res.user.email} logged in."); return res.session, f"Login successful! Welcome {res.user.email}."
        elif hasattr(res, 'error') and res.error: return None, f"Login failed: {res.error.message}"
        else: return None, "Login failed. Check credentials or confirm email."
    except Exception as e: return None, f"An unexpected error during login: {str(e)}"
def logout_user(session_state):
    if not supabase: return "Supabase client not initialized.", session_state, []
    if session_state and hasattr(session_state, 'user') and session_state.user:
        try: supabase.auth.sign_out(); print("User logged out from Supabase."); return "Logout successful.", None, []
        except Exception as e: print(f"Error during Supabase sign_out: {str(e)}"); return f"Logout error: {str(e)}", None, []
    return "No active session.", session_state, []
def get_user_role(user_session):
    if user_session and hasattr(user_session, 'user') and user_session.user:
        if ADMIN_EMAIL and user_session.user.email == ADMIN_EMAIL: return 'admin'
        return 'user'
    return None

# --- Data Fetching (User) ---
def fetch_equipments(department_filter, search_query):
    if not supabase: return pd.DataFrame(columns=['ID', '장비명 (Name)', '부서 (Department)', '총 수량 (Total)', '대여 가능 수량 (Available)']), "Supabase client not initialized."
    try:
        query = supabase.table("equipments").select("id, name, department, quantity, available_quantity")
        if department_filter and department_filter != "전체": query = query.eq("department", department_filter)
        if search_query: query = query.or_(f"name.ilike.%{search_query}%,id.eq.{search_query.upper()}")
        response = query.execute()
        if response.data: df = pd.DataFrame(response.data)[['id', 'name', 'department', 'quantity', 'available_quantity']]; df.columns = ['ID', '장비명 (Name)', '부서 (Department)', '총 수량 (Total)', '대여 가능 수량 (Available)']; return df, "장비 목록을 성공적으로 불러왔습니다."
        else: return pd.DataFrame(columns=['ID', '장비명 (Name)', '부서 (Department)', '총 수량 (Total)', '대여 가능 수량 (Available)']), "조건에 맞는 장비가 없습니다."
    except Exception as e:
        error_message = str(e); print(f"Error fetching equipments: {e}")
        if "JWT" in error_message or "token" in error_message or "authorization" in error_message.lower(): return pd.DataFrame(), f"데이터 조회 중 인증 오류: {error_message}."
        return pd.DataFrame(), f"장비 목록 조회 중 오류 발생: {error_message}"

# --- Rental Logic ---
def process_rental_request(selected_equipment_ids, start_date_str, end_date_str, borrower_name, purpose_text, user_session):
    if not supabase: return "Supabase client not initialized.", selected_equipment_ids
    if not user_session or not hasattr(user_session, 'user'): return "오류: 사용자 세션이 없습니다. 다시 로그인 해주세요.", selected_equipment_ids
    if not selected_equipment_ids: return "오류: 대여할 장비가 선택되지 않았습니다.", selected_equipment_ids
    user_id = user_session.user.id; equipment_id_to_rent = selected_equipment_ids[0]
    if not all([start_date_str, end_date_str, borrower_name, purpose_text]): return "오류: 모든 필드(시작일, 종료일, 대여자명, 사용 목적)를 입력해야 합니다.", selected_equipment_ids
    try: start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date(); end_date_obj = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError: return "오류: 날짜 형식이 잘못되었습니다. YYYY-MM-DD 형식으로 입력해주세요.", selected_equipment_ids
    if start_date_obj < date.today(): return "오류: 대여 시작일은 오늘 또는 그 이후여야 합니다.", selected_equipment_ids
    if end_date_obj < start_date_obj: return "오류: 대여 종료일은 시작일보다 이후여야 합니다.", selected_equipment_ids
    try:
        eq_response = supabase.table("equipments").select("name, available_quantity, quantity").eq("id", equipment_id_to_rent).single().execute()
        if not eq_response.data: return f"오류: 장비 ID '{equipment_id_to_rent}' 정보를 찾을 수 없습니다.", selected_equipment_ids
        equipment_name = eq_response.data.get('name', equipment_id_to_rent)
        if eq_response.data['available_quantity'] < 1: return f"오류: 장비 '{equipment_name}'는 현재 대여 가능 수량이 없습니다.", selected_equipment_ids
        conflict_response = supabase.table("rentals").select("id", count="exact").eq("equipment_id", equipment_id_to_rent).eq("status", "confirmed").lte("start_date", end_date_str).gte("end_date", start_date_str).execute()
        if conflict_response.count > 0: return f"오류: 선택한 장비 '{equipment_name}'는 해당 기간 ({start_date_str} ~ {end_date_str})에 이미 대여 중입니다. 다른 날짜를 선택해주세요.", selected_equipment_ids
        rental_data = {"equipment_id": equipment_id_to_rent, "start_date": start_date_str, "end_date": end_date_str, "borrower_name": borrower_name, "purpose": purpose_text, "user_id": user_id, "status": "confirmed"}
        insert_res = supabase.table("rentals").insert(rental_data).execute()
        if not (insert_res.data and len(insert_res.data) > 0): print(f"Rental insert may have failed: {insert_res}") # Log potential issue
        new_available_quantity = eq_response.data['available_quantity'] - 1
        update_eq_res = supabase.table("equipments").update({"available_quantity": new_available_quantity}).eq("id", equipment_id_to_rent).execute()
        if not (update_eq_res.data and len(update_eq_res.data) > 0): print(f"Warning: Equip quantity update for {equipment_id_to_rent} failed: {update_eq_res}")
        return f"성공: 장비 '{equipment_name}' 대여 신청이 완료되었습니다. (기간: {start_date_str} ~ {end_date_str})", []
    except Exception as e: 
        print(f"Error processing rental request: {e}, {type(e)}")
        err_msg = str(e)
        if "violates row-level security policy" in err_msg: 
            return f"오류: 보안 정책 위반 ({err_msg}).", selected_equipment_ids
        if "check_constraint" in err_msg and "available_quantity" in err_msg: 
            return "오류: 데이터베이스 제약 조건 위반 (수량).", selected_equipment_ids
        return f"대여 처리 중 서버 오류 발생: {err_msg}", selected_equipment_ids

# --- Admin Specific Functions ---
def fetch_all_equipments_admin_action(user_session): # Renamed to avoid conflict with component
    if not supabase: return pd.DataFrame(columns=['ID', '장비명', '부서', '총량', '가용량']), "Supabase client not initialized."
    if get_user_role(user_session) != 'admin': return pd.DataFrame(columns=['ID', '장비명', '부서', '총량', '가용량']), "관리자 권한이 필요합니다."
    try:
        response = supabase.table("equipments").select("id, name, department, quantity, available_quantity").order("id", desc=False).execute()
        if response.data: df = pd.DataFrame(response.data)[['id', 'name', 'department', 'quantity', 'available_quantity']]; df.columns = ['ID', '장비명', '부서', '총량', '가용량']; return df, "모든 장비 목록을 성공적으로 불러왔습니다."
        else: return pd.DataFrame(columns=['ID', '장비명', '부서', '총량', '가용량']), "등록된 장비가 없습니다."
    except Exception as e: print(f"Error in fetch_all_equipments_admin_action: {e}"); return pd.DataFrame(columns=['ID', '장비명', '부서', '총량', '가용량']), f"관리자 장비 조회 오류: {str(e)}"

def add_equipment_admin_action(eq_id, name, dept, qty_str, user_session):
    if get_user_role(user_session) != 'admin': return "관리자 권한 필요.", eq_id, name, dept, qty_str
    if not all([eq_id, name, dept, qty_str]): return "모든 필드(ID, 이름, 부서, 수량)를 입력해야 합니다.", eq_id, name, dept, qty_str
    try: qty = int(qty_str)
    except ValueError: return "수량은 숫자여야 합니다.", eq_id, name, dept, qty_str
    if qty <= 0: return "수량은 0보다 커야 합니다.", eq_id, name, dept, qty_str
    processed_eq_id = eq_id.strip().upper()
    if not processed_eq_id: return "ID는 공백일 수 없습니다.", processed_eq_id, name, dept, qty_str
    try:
        if supabase.table("equipments").select("id", count="exact").eq("id", processed_eq_id).execute().count > 0: return f"오류: 장비 ID '{processed_eq_id}'는 이미 존재합니다.", processed_eq_id, name, dept, qty_str
        data = {"id": processed_eq_id, "name": name, "department": dept, "quantity": qty, "available_quantity": qty}
        supabase.table("equipments").insert(data).execute()
        return f"성공: 장비 '{name}' (ID: {processed_eq_id}) 추가 완료.", None, None, None, None # Clear fields
    except Exception as e: print(f"Error in add_equipment_admin_action: {e}"); return f"장비 추가 오류: {str(e)}", processed_eq_id, name, dept, qty_str

def update_equipment_admin_action(original_item_state, new_id_str, name, dept, new_qty_str, user_session):
    if get_user_role(user_session) != 'admin': return "관리자 권한 필요.", original_item_state, new_id_str, name, dept, new_qty_str
    if not original_item_state or 'ID' not in original_item_state: return "수정할 장비를 먼저 목록에서 선택하세요.", original_item_state, new_id_str, name, dept, new_qty_str
    original_id = original_item_state['ID']
    if not all([new_id_str, name, dept, new_qty_str]): return "모든 필드(ID, 이름, 부서, 수량)를 입력해야 합니다.", original_item_state, new_id_str, name, dept, new_qty_str
    try: new_qty = int(new_qty_str)
    except ValueError: return "수량은 숫자여야 합니다.", original_item_state, new_id_str, name, dept, new_qty_str
    if new_qty < 0: return "수량은 0 이상이어야 합니다.", original_item_state, new_id_str, name, dept, new_qty_str

    processed_new_id = new_id_str.strip().upper()
    if not processed_new_id: return "ID는 공백일 수 없습니다.", original_item_state, processed_new_id, name, dept, new_qty_str

    try:
        current_eq_data = supabase.table("equipments").select("quantity, available_quantity").eq("id", original_id).single().execute().data
        if not current_eq_data: return f"오류: 원본 장비 ID '{original_id}'를 찾을 수 없습니다.", original_item_state, processed_new_id, name, dept, new_qty_str

        rented_qty = current_eq_data['quantity'] - current_eq_data['available_quantity']
        new_available_qty = new_qty - rented_qty
        if new_available_qty < 0: return f"오류: 새 총 수량({new_qty})이 현재 대여된 수량({rented_qty})보다 적을 수 없습니다. 최소 {rented_qty} 이상이어야 합니다.", original_item_state, processed_new_id, name, dept, new_qty_str

        update_payload = {"name": name, "department": dept, "quantity": new_qty, "available_quantity": new_available_qty}

        # Handle ID change: If new ID is different and already exists (and it's not the original item), block.
        if processed_new_id != original_id:
            existing_item_with_new_id = supabase.table("equipments").select("id").eq("id", processed_new_id).execute().data
            if existing_item_with_new_id and len(existing_item_with_new_id) > 0:
                return f"오류: 변경하려는 새 ID '{processed_new_id}'가 이미 다른 장비에 사용 중입니다.", original_item_state, processed_new_id, name, dept, new_qty_str
            update_payload["id"] = processed_new_id # Add new ID to payload if it's changing

        supabase.table("equipments").update(update_payload).eq("id", original_id).execute()
        return f"성공: 장비 ID '{original_id}' 정보가 업데이트되었습니다. (새 ID: {processed_new_id})", None, None, None, None, None # Clear fields & selection state
    except Exception as e: print(f"Error in update_equipment_admin_action: {e}"); return f"장비 수정 오류: {str(e)}", original_item_state, processed_new_id, name, dept, new_qty_str

# --- Main Gradio Application ---
if __name__ == "__main__":
    if not supabase:
        print("Gradio app launch failed: Supabase client not initialized.")
        fallback_demo = gr.Blocks(title="오류")
        with fallback_demo: 
            gr.Markdown("Supabase 연결 실패.")
            fallback_demo.launch()
            exit()

    print("Initializing Gradio app...")
    demo = gr.Blocks(title="장비 대여 및 관리 앱", theme=gr.themes.Soft())

    with demo:
        user_session_var = gr.State(None)
        selected_equipment_to_rent_var = gr.State([])
        current_search_df_state = gr.State(pd.DataFrame())
        admin_all_equipments_df_state = gr.State(pd.DataFrame())
        selected_equipment_for_edit_state = gr.State(None)

        gr.Markdown("# 🇰🇷 장비 대여 및 관리 시스템 🇰🇷")
        if not ADMIN_EMAIL: gr.Warning("ADMIN_EMAIL 환경 변수가 설정되지 않았습니다. 관리자 기능이 제한될 수 있습니다.")

        with gr.Tabs(elem_id="main_tabs") as main_tabs:
            with gr.TabItem("🔎 장비 조회 및 검색", id="search_tab"):
                gr.Markdown("## 장비 조회 및 검색")
                with gr.Row(): search_dept_dropdown = gr.Dropdown(label="부서 선택", choices=["전체", "물리과", "화학과", "IT과", "공과대학", "공용"], value="전체"); search_term_input = gr.Textbox(label="검색어 (ID 또는 이름)", placeholder="예: EQP-001 또는 현미경")
                search_button = gr.Button("🔄 장비 조회", variant="primary")
                search_results_df = gr.DataFrame(label="조회된 장비 목록", headers=['ID', '장비명 (Name)', '부서 (Department)', '총 수량 (Total)', '대여 가능 수량 (Available)'], datatype=['str', 'str', 'str', 'number', 'number'], interactive=True, row_count=(5,"dynamic"), col_count=(5,"fixed"))
                search_status_output = gr.Textbox(label="조회 상태", interactive=False)
                gr.Markdown("---"); selected_items_display = gr.Textbox(label="선택된 장비 (대여 가능 여부 확인)", interactive=False, lines=1); request_rental_button = gr.Button("✅ 선택 장비로 대여 신청 진행하기", variant="secondary", interactive=False)

            with gr.TabItem("📝 장비 대여", id="rental_tab"):
                gr.Markdown("## 장비 대여 신청"); rental_selected_display = gr.Textbox(label="선택된 대여 장비 정보 (자동 업데이트)", lines=4, interactive=False)
                with gr.Row(): rental_start_date_input = gr.Textbox(label="대여 시작일 (YYYY-MM-DD)", placeholder=date.today().isoformat(), value=date.today().isoformat()); rental_end_date_input = gr.Textbox(label="대여 종료일 (YYYY-MM-DD)", placeholder=(date.today() + timedelta(days=7)).isoformat(), value=(date.today() + timedelta(days=7)).isoformat())
                rental_borrower_name_input = gr.Textbox(label="대여자 이름", placeholder="예: 홍길동"); rental_purpose_input = gr.Textbox(label="사용 목적", lines=2, placeholder="예: OO실험 강의용")
                confirm_rental_button = gr.Button("📲 대여 신청 확정 및 제출", variant="primary"); rental_status_output = gr.Textbox(label="대여 신청 상태", interactive=False, lines=2)

            auth_tab_item_obj = gr.TabItem("🔑 사용자 인증", id="auth_tab")
            with auth_tab_item_obj:
                gr.Markdown("## 사용자 인증 센터")
                with gr.Column(visible=True, elem_id="auth_forms_group_elem") as auth_forms_group:
                    gr.Markdown("### 신규 사용자 회원가입"); signup_email_input = gr.Textbox(label="이메일", placeholder="user@example.com"); signup_password_input = gr.Textbox(label="비밀번호", type="password"); signup_confirm_password_input = gr.Textbox(label="비밀번호 확인", type="password"); signup_button = gr.Button("회원가입"); signup_status_output = gr.Textbox(label="가입 상태", interactive=False)
                    gr.Markdown("---"); gr.Markdown("### 사용자 로그인"); login_email_input = gr.Textbox(label="이메일", placeholder="user@example.com 또는 admin@example.com"); login_password_input = gr.Textbox(label="비밀번호", type="password"); login_button = gr.Button("로그인"); login_status_output = gr.Textbox(label="로그인 상태", interactive=False)
                with gr.Column(visible=False, elem_id="user_info_group_elem") as user_info_group:
                    gr.Markdown("### 사용자 정보"); current_user_display = gr.Textbox(label="현재 사용자", interactive=False, lines=4, max_lines=5); logout_button_auth_tab = gr.Button("로그아웃"); logout_status_auth_tab_output = gr.Textbox(label="로그아웃 상태", interactive=False)

            admin_management_tab_item_obj = gr.TabItem("⚙️ 장비 관리 (관리자)", id="management_tab", visible=False)
            with admin_management_tab_item_obj:
                gr.Markdown("## 장비 관리 시스템 (관리자 모드)")
                admin_status_output = gr.Textbox(label="관리자 작업 상태", interactive=False, lines=2, max_lines=5)
                with gr.Tabs(elem_id="admin_sub_tabs") as admin_sub_tabs:
                    with gr.TabItem("📋 모든 장비 현황 조회", id="admin_view_all_tab"):
                        admin_refresh_equip_list_button = gr.Button("🔄 모든 장비 목록 새로고침")
                        admin_equipments_df_display = gr.DataFrame(label="시스템 등록 장비 목록", headers=['ID', '장비명', '부서', '총량', '가용량'], datatype=['str', 'str', 'str', 'number', 'number'], interactive=True, row_count=(10, "dynamic"), col_count=(5,"fixed"))
                    with gr.TabItem("➕➖ 장비 추가/수정", id="admin_add_edit_tab"):
                        gr.Markdown("### 장비 정보 입력/수정 (목록에서 선택 시 자동 입력)")
                        admin_edit_id_input = gr.Textbox(label="장비 ID (필수, 고유값)", placeholder="예: EQP-XYZ-001")
                        admin_edit_name_input = gr.Textbox(label="장비명 (필수)", placeholder="예: 고성능 오실로스코프")
                        admin_edit_dept_dropdown = gr.Dropdown(label="부서 (필수)", choices=["물리과", "화학과", "IT과", "공과대학", "공용"], value="공용")
                        admin_edit_qty_input = gr.Textbox(label="총 수량 (필수, 숫자)", placeholder="예: 5")
                        with gr.Row(): admin_add_button = gr.Button("➕ 새 장비 추가", variant="primary"); admin_update_button = gr.Button("💾 선택 장비 정보 수정", variant="secondary"); admin_clear_fields_button = gr.Button("✨ 입력 초기화")
                gr.Markdown("---"); logout_button_admin_tab = gr.Button("🔒 관리자 로그아웃"); logout_status_admin_tab_output = gr.Textbox(label="로그아웃 상태", interactive=False)

            # --- Search Tab Event Handlers ---
            search_results_df.change(lambda x: x, inputs=[search_results_df], outputs=[current_search_df_state])
            search_button.click(fetch_equipments, inputs=[search_dept_dropdown, search_term_input], outputs=[search_results_df, search_status_output])
            def df_select_for_rental(df_state_val, evt: gr.SelectData):
                if evt.selected and not df_state_val.empty:
                    row_idx=evt.index[0]
                    if 0 <= row_idx < len(df_state_val):
                        sel_id=df_state_val.iloc[row_idx]['ID']; sel_name=df_state_val.iloc[row_idx]['장비명 (Name)']; avail_qty=int(df_state_val.iloc[row_idx]['대여 가능 수량 (Available)'])
                        if avail_qty > 0: request_rental_button.interactive=True; return f"선택: {sel_name} (ID: {sel_id}, 잔여: {avail_qty})", [sel_id], gr.update(interactive=True)
                        else: return f"{sel_name} (ID: {sel_id}) 대여 불가 (잔여:0).", [], gr.update(interactive=False)
                return "선택된 장비 없음.", [], gr.update(interactive=False)
            search_results_df.select(df_select_for_rental, inputs=[current_search_df_state], outputs=[selected_items_display, selected_equipment_to_rent_var, request_rental_button])
            request_rental_button.click(lambda sel_ids, user_sess, tabs: gr.Tabs(selected="rental_tab") if user_sess and sel_ids else gr.Warning("로그인 및 장비 선택 필요") or tabs, inputs=[selected_equipment_to_rent_var, user_session_var, main_tabs], outputs=[main_tabs])

            # --- Rental Tab Event Handlers ---
            selected_equipment_to_rent_var.change(lambda sel_ids: supabase.table("equipments").select("id,name,department,available_quantity").eq("id",sel_ids[0]).single().execute().data if sel_ids and supabase else "장비 선택 필요", inputs=[selected_equipment_to_rent_var], outputs=[rental_selected_display]) # Simplified display for now
            confirm_rental_button.click(process_rental_request, inputs=[selected_equipment_to_rent_var, rental_start_date_input, rental_end_date_input, rental_borrower_name_input, rental_purpose_input, user_session_var], outputs=[rental_status_output, selected_equipment_to_rent_var])

            # --- Admin Tab Event Handlers ---
            admin_refresh_equip_list_button.click(fetch_all_equipments_admin_action, inputs=[user_session_var], outputs=[admin_all_equipments_df_state, admin_status_output])
            admin_all_equipments_df_state.change(lambda df_data: df_data, inputs=[admin_all_equipments_df_state], outputs=[admin_equipments_df_display]) # Link state to display component

            def admin_df_select_for_edit(df_admin_data, evt: gr.SelectData):
                if evt.selected and not df_admin_data.empty:
                    row_idx = evt.index[0]
                    if 0 <= row_idx < len(df_admin_data):
                        sel_row = df_admin_data.iloc[row_idx].to_dict()
                        gr.Info(f"{sel_row['장비명']} (ID: {sel_row['ID']}) 선택됨. 수정 탭에서 정보 확인.")
                        return sel_row, sel_row['ID'], sel_row['장비명'], sel_row['부서'], str(sel_row['총량']), gr.Tabs(selected="admin_add_edit_tab")
                return None, None, None, None, None, admin_sub_tabs # No change to sub_tab if error
            admin_equipments_df_display.select(admin_df_select_for_edit, inputs=[admin_all_equipments_df_state], outputs=[selected_equipment_for_edit_state, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, admin_sub_tabs])

            def add_equip_refresh_list(eq_id, name, dept, qty_str, sess):
                feedback, out_id, out_name, out_dept, out_qty = add_equipment_admin_action(eq_id, name, dept, qty_str, sess)
                if "성공" in feedback: gr.Info(feedback); df_new, _ = fetch_all_equipments_admin_action(sess); return feedback, out_id, out_name, out_dept, out_qty, df_new
                else: gr.Error(feedback); return feedback, out_id, out_name, out_dept, out_qty, admin_all_equipments_df_state # Keep old df state on error
            admin_add_button.click(add_equip_refresh_list, inputs=[admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, user_session_var], outputs=[admin_status_output, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, admin_all_equipments_df_state])

            def update_equip_refresh_list(sel_state, new_id, name, dept, new_qty_str, sess):
                feedback, out_sel_state, out_id, out_name, out_dept, out_qty = update_equipment_admin_action(sel_state, new_id, name, dept, new_qty_str, sess)
                if "성공" in feedback: gr.Info(feedback); df_new, _ = fetch_all_equipments_admin_action(sess); return feedback, out_sel_state, out_id, out_name, out_dept, out_qty, df_new
                else: gr.Error(feedback); return feedback, out_sel_state, out_id, out_name, out_dept, out_qty, admin_all_equipments_df_state
            admin_update_button.click(update_equip_refresh_list, inputs=[selected_equipment_for_edit_state, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, user_session_var], outputs=[admin_status_output, selected_equipment_for_edit_state, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, admin_all_equipments_df_state])

            def clear_admin_form_fields_action(): return None, "", "", "공용", "", "입력 필드가 초기화되었습니다."
            admin_clear_fields_button.click(clear_admin_form_fields_action, outputs=[selected_equipment_for_edit_state, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, admin_status_output])

            # --- Auth Event Handlers ---
            signup_button.click(signup_user, inputs=[signup_email_input, signup_password_input, signup_confirm_password_input], outputs=[signup_status_output])
            def handle_login_ui_updates(email, pw):
                sess_data, msg = login_user(email, pw); role = get_user_role(sess_data)
                if sess_data:
                    gr.Info(f"환영합니다, {sess_data.user.email}! (역할: {role})")
                    if role == 'admin': df_admin_equip, msg_admin_equip = fetch_all_equipments_admin_action(sess_data); return msg, sess_data, gr.update(visible=False), gr.update(True), gr.update(visible=False), gr.update(visible=True), gr.Tabs(selected="management_tab"), df_admin_equip, msg_admin_equip
                    else: return msg, sess_data, gr.update(visible=False), gr.update(True), gr.update(visible=True), gr.update(visible=False), gr.Tabs(selected="search_tab"), pd.DataFrame(columns=['ID', '장비명', '부서', '총량', '가용량']), "" # Clear admin df for non-admins
                else: gr.Error(msg); return msg, None, gr.update(visible=True), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), main_tabs, pd.DataFrame(columns=['ID', '장비명', '부서', '총량', '가용량']), ""
            login_button.click(handle_login_ui_updates, inputs=[login_email_input, login_password_input], outputs=[login_status_output, user_session_var, auth_forms_group, user_info_group, auth_tab_item_obj, admin_management_tab_item_obj, main_tabs, admin_all_equipments_df_state, admin_status_output])

            def universal_logout_ui_updates(curr_sess):
                logout_msg, new_sess, sel_eq_cleared = logout_user(curr_sess); gr.Info(logout_msg)
                return (logout_msg, new_sess, gr.update(visible=True), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.Tabs(selected="search_tab"), sel_eq_cleared, pd.DataFrame(columns=['ID', '장비명', '부서', '총량', '가용량']), None, "", "", "공용", "", "로그아웃됨.")
            logout_button_auth_tab.click(universal_logout_ui_updates, inputs=[user_session_var], outputs=[logout_status_auth_tab_output, user_session_var, auth_forms_group, user_info_group, auth_tab_item_obj, admin_management_tab_item_obj, main_tabs, selected_equipment_to_rent_var, admin_all_equipments_df_state, selected_equipment_for_edit_state, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, admin_status_output])
            logout_button_admin_tab.click(universal_logout_ui_updates, inputs=[user_session_var], outputs=[logout_status_admin_tab_output, user_session_var, auth_forms_group, user_info_group, auth_tab_item_obj, admin_management_tab_item_obj, main_tabs, selected_equipment_to_rent_var, admin_all_equipments_df_state, selected_equipment_for_edit_state, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, admin_status_output])

            user_session_var.change(lambda s: f"Email: {s.user.email}\nRole: {get_user_role(s)}\nExpires: {datetime.fromtimestamp(s.expires_at).strftime('%Y-%m-%d %H:%M:%S') if s and s.expires_at else 'N/A'}" if s and hasattr(s,'user') and s.user else "로그인되지 않음.", inputs=[user_session_var], outputs=[current_user_display])

        demo.launch(debug=True, share=False)
        print("Gradio app launched with full Admin Management Tab.")

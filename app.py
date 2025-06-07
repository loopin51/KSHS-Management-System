import os # Keep os for ADMIN_EMAIL
import gradio as gr
# pandas and datetime might be needed for UI logic or data manipulation within app.py, keep them for now.
import pandas as pd
from datetime import date, datetime, timedelta
import re # Retaining re

from auth_utils import (
    is_valid_email, # Though not directly used by app.py event handlers, useful if UI logic needs it
    signup_user,
    login_user,
    logout_user,
    get_user_role
)
from db_utils import (
    get_supabase_client,
    get_supabase_init_error,
    fetch_equipments,
    process_rental_request,
    fetch_all_equipments_admin, # Renamed in db_utils
    add_equipment_admin,       # Renamed in db_utils
    update_equipment_admin,     # Renamed in db_utils
    fetch_all_rental_details
)
# Load dotenv here if ADMIN_EMAIL is the only thing needed from .env in app.py
# If db_utils already loads it, it might not be necessary here unless for other env vars.
# For now, assume ADMIN_EMAIL is loaded directly.
from dotenv import load_dotenv
load_dotenv() # Ensure ADMIN_EMAIL is loaded

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
supabase_client = get_supabase_client()
supabase_init_error = get_supabase_init_error()

# --- Gradio Event Handlers ---

# Search Tab
def df_select_for_rental(df_state_val: pd.DataFrame, evt: gr.SelectData) -> tuple:
    if evt.selected and df_state_val is not None and not df_state_val.empty:
        row_idx = evt.index[0]
        if 0 <= row_idx < len(df_state_val):
            sel_id = df_state_val.iloc[row_idx]['ID']
            sel_name = df_state_val.iloc[row_idx]['장비명 (Name)']
            avail_qty = int(df_state_val.iloc[row_idx]['대여 가능 수량 (Available)'])
            if avail_qty > 0:
                return f"선택: {sel_name} (ID: {sel_id}, 잔여: {avail_qty})", [sel_id], gr.update(interactive=True)
            else:
                return f"{sel_name} (ID: {sel_id}) 대여 불가 (잔여:0).", [], gr.update(interactive=False)
    return "선택된 장비 없음.", [], gr.update(interactive=False)

def handle_request_rental_navigation(sel_ids: list, user_sess: Any, current_tabs: gr.Tabs) -> gr.Tabs:
    if user_sess and sel_ids:
        return gr.Tabs(selected="rental_tab")
    else:
        gr.Warning("로그인 및 장비 선택 필요")
        return current_tabs

# Rental Tab
def update_rental_selected_display(sel_ids: list) -> str:
    if sel_ids and supabase_client:
        try:
            # Ensure sel_ids[0] is used, as it's a list of one item
            response = supabase_client.table("equipments").select("id, name, department, available_quantity").eq("id", sel_ids[0]).single().execute()
            if response.data:
                return f"ID: {response.data['id']}\n이름: {response.data['name']}\n부서: {response.data['department']}\n대여 가능: {response.data['available_quantity']}"
            else:
                return "선택된 장비 정보를 찾을 수 없습니다."
        except Exception as e:
            print(f"Error fetching equipment details for rental display: {e}")
            return "장비 정보 조회 중 오류 발생."
    return "장비 선택 필요"

# Admin Tab
def handle_fetch_all_equip_admin(user_sess: Any) -> tuple[pd.DataFrame, str]:
    if get_user_role(user_sess, ADMIN_EMAIL) != 'admin':
        return pd.DataFrame(columns=['ID', '장비명', '부서', '총량', '가용량']), "관리자 권한이 필요합니다."
    return fetch_all_equipments_admin()

def admin_df_select_for_edit(df_admin_data: pd.DataFrame, evt: gr.SelectData) -> tuple:
    if evt.selected and df_admin_data is not None and not df_admin_data.empty:
        row_idx = evt.index[0]
        if 0 <= row_idx < len(df_admin_data):
            sel_row = df_admin_data.iloc[row_idx].to_dict()
            gr.Info(f"{sel_row['장비명']} (ID: {sel_row['ID']}) 선택됨. 수정 탭에서 정보 확인.")
            return sel_row, sel_row['ID'], sel_row['장비명'], sel_row['부서'], str(sel_row['총량']), gr.Tabs(selected="admin_add_edit_tab")
    return None, None, None, None, None, gr.Tabs() # Return empty Tabs to avoid error, or current state

def add_equip_refresh_list(eq_id: str, name: str, dept: str, qty_str: str, sess: Any, current_admin_df: pd.DataFrame) -> tuple:
    if get_user_role(sess, ADMIN_EMAIL) != 'admin':
        return "관리자 권한 필요.", eq_id, name, dept, qty_str, current_admin_df
    feedback, out_id, out_name, out_dept, out_qty = add_equipment_admin(eq_id, name, dept, qty_str)
    if "성공" in feedback:
        gr.Info(feedback)
        df_new, msg = handle_fetch_all_equip_admin(sess)
        return feedback, out_id, out_name, out_dept, out_qty, df_new
    else:
        gr.Error(feedback)
        return feedback, out_id, out_name, out_dept, out_qty, current_admin_df

def update_equip_refresh_list(sel_state: dict, new_id: str, name: str, dept: str, new_qty_str: str, sess: Any, current_admin_df: pd.DataFrame) -> tuple:
    if get_user_role(sess, ADMIN_EMAIL) != 'admin':
        return "관리자 권한 필요.", sel_state, new_id, name, dept, new_qty_str, current_admin_df
    feedback, out_sel_state, out_id, out_name, out_dept, out_qty = update_equipment_admin(sel_state, new_id, name, dept, new_qty_str)
    if "성공" in feedback:
        gr.Info(feedback)
        df_new, msg = handle_fetch_all_equip_admin(sess)
        return feedback, out_sel_state, out_id, out_name, out_dept, out_qty, df_new
    else:
        gr.Error(feedback)
        return feedback, out_sel_state, out_id, out_name, out_dept, out_qty, current_admin_df

def clear_admin_form_fields_action() -> tuple:
    return None, "", "", "공용", "", "입력 필드가 초기화되었습니다."

# Auth Tab
def handle_signup_action(email: str, pw: str, conf_pw: str) -> str:
    return signup_user(supabase_client, email, pw, conf_pw)

def handle_login_ui_updates(email: str, pw: str, current_admin_df: pd.DataFrame, current_main_tabs: gr.Tabs) -> tuple:
    sess_data, msg = login_user(supabase_client, email, pw)
    role = get_user_role(sess_data, ADMIN_EMAIL)
    if sess_data:
        gr.Info(f"환영합니다, {sess_data.user.email}! (역할: {role})")
        df_admin_equip_val = current_admin_df
        msg_admin_equip_val = ""
        if role == 'admin':
            df_admin_equip_val, msg_admin_equip_val = handle_fetch_all_equip_admin(sess_data)
        return msg, sess_data, gr.update(visible=False), gr.update(True), gr.update(visible=False), gr.update(visible=True if role == 'admin' else False), gr.Tabs(selected="management_tab" if role == 'admin' else "search_tab"), df_admin_equip_val, msg_admin_equip_val
    else:
        gr.Error(msg)
        return msg, None, gr.update(visible=True), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), current_main_tabs, current_admin_df, ""

def universal_logout_ui_updates(curr_sess: Any) -> tuple:
    logout_msg, new_sess, sel_eq_cleared = logout_user(supabase_client, curr_sess)
    gr.Info(logout_msg)
    empty_admin_df = pd.DataFrame(columns=['ID', '장비명', '부서', '총량', '가용량'])
    # Returns: msg, new_session, auth_forms_visible, user_info_visible, auth_tab_visible, admin_tab_visible, main_tab_selected,
    #          cleared_rental_selection, new_admin_df, cleared_admin_edit_state, admin_fields..., admin_status
    return (logout_msg, new_sess, gr.update(visible=True), gr.update(visible=False),
            gr.update(visible=True), gr.update(visible=False), gr.Tabs(selected="search_tab"),
            sel_eq_cleared, empty_admin_df, None, "", "", "공용", "", "로그아웃됨.")

def update_user_display(s: Any) -> str:
    if s and hasattr(s, 'user') and s.user:
        role = get_user_role(s, ADMIN_EMAIL)
        expires_at_str = "N/A"
        if hasattr(s, 'expires_at') and s.expires_at:
            try:
                # Check if s.expires_at is already a datetime object or needs conversion
                if isinstance(s.expires_at, (int, float)):
                    expires_at_str = datetime.fromtimestamp(s.expires_at).strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(s.expires_at, datetime):
                     expires_at_str = s.expires_at.strftime('%Y-%m-%d %H:%M:%S')
                # Add other type checks if necessary, e.g., for string representations of dates
            except Exception as e:
                print(f"Error formatting expires_at: {e}")
        return f"Email: {s.user.email}\nRole: {role}\nExpires: {expires_at_str}"
    return "로그인되지 않음."

# Handler for fetching and displaying all rental details
def handle_fetch_all_rentals_ui():
    # No user_session needed if visible to all, and db_utils function doesn't require it.
    # supabase_client is global in app.py
    if not supabase_client: # Check if client is available
         init_err = get_supabase_init_error() or "Supabase client not initialized."
         return pd.DataFrame(columns=["대여자 (Borrower)", "장비명 (Equipment Name)", "수량 (Quantity)", "대여 시작일 (Start Date)", "반납 기한 (End Date)", "상태 (Status)"]), f"오류: {init_err}"

    df, message = fetch_all_rental_details() # From db_utils
    if "오류" in message or "Error" in message: # A bit generic, but works for now
        gr.Error(message)
    else:
        gr.Info(message)
    return df, message

# --- Main Gradio Application ---
if __name__ == "__main__":
    if not supabase_client: # Use the client obtained from db_utils
        print(f"Gradio app launch failed: {supabase_init_error}")
        fallback_demo = gr.Blocks(title="오류")
        with fallback_demo: 
            gr.Markdown(f"Supabase 연결 실패: {supabase_init_error}") # Show specific error
            fallback_demo.launch()
            # exit() # Keep or remove exit based on desired behavior
        # If using exit(), make sure it's appropriate for the execution environment.
        # For now, allow Gradio to handle the launch failure message.
    else:
        print("Initializing Gradio app with refactored logic...")
    demo = gr.Blocks(title="장비 대여 및 관리 앱", theme=gr.themes.Soft())

    with demo:
        user_session_var = gr.State(None)
        selected_equipment_to_rent_var = gr.State([]) # Stores list of selected equipment IDs for rental
        current_search_df_state = gr.State(pd.DataFrame(columns=['ID', '장비명 (Name)', '부서 (Department)', '총 수량 (Total)', '대여 가능 수량 (Available)']))
        admin_all_equipments_df_state = gr.State(pd.DataFrame(columns=['ID', '장비명', '부서', '총량', '가용량'])) # For admin view
        selected_equipment_for_edit_state = gr.State(None) # Stores dict of row data for editing
        all_rentals_df_state = gr.State(pd.DataFrame(columns=["대여자 (Borrower)", "장비명 (Equipment Name)", "수량 (Quantity)", "대여 시작일 (Start Date)", "반납 기한 (End Date)", "상태 (Status)"]))

        gr.Markdown("# 🇰🇷 장비 대여 및 관리 시스템 🇰🇷")
        if not ADMIN_EMAIL: gr.Warning("ADMIN_EMAIL 환경 변수가 설정되지 않았습니다. 관리자 기능이 제한될 수 있습니다.")

        with gr.Tabs(elem_id="main_tabs") as main_tabs:
            with gr.TabItem("🔎 장비 조회 및 검색", id="search_tab"):
                gr.Markdown("## 장비 조회 및 검색")
                with gr.Row(): search_dept_dropdown = gr.Dropdown(label="부서 선택", choices=["전체", "물리과", "화학과", "IT과", "공과대학", "공용"], value="전체"); search_term_input = gr.Textbox(label="검색어 (ID 또는 이름)", placeholder="예: EQP-001 또는 현미경")
                search_button = gr.Button("🔄 장비 조회", variant="primary")
                search_results_df = gr.DataFrame(label="조회된 장비 목록", headers=['ID', '장비명 (Name)', '부서 (Department)', '총 수량 (Total)', '대여 가능 수량 (Available)'], value=pd.DataFrame(columns=['ID', '장비명 (Name)', '부서 (Department)', '총 수량 (Total)', '대여 가능 수량 (Available)']), datatype=['str', 'str', 'str', 'number', 'number'], interactive=True, row_count=(5,"dynamic"), col_count=(5,"fixed"))
                search_status_output = gr.Textbox(label="조회 상태", interactive=False)
                gr.Markdown("---"); selected_items_display = gr.Textbox(label="선택된 장비 (대여 가능 여부 확인)", interactive=False, lines=1); request_rental_button = gr.Button("✅ 선택 장비로 대여 신청 진행하기", variant="secondary", interactive=False)

                gr.Markdown("---") # Separator
                gr.Markdown("## 🗓️ 전체 대여 현황")
                show_all_rentals_button = gr.Button("🔄 전체 대여 현황 보기/새로고침", variant="secondary")
                all_rentals_status_output = gr.Textbox(label="대여 현황 조회 상태", interactive=False, lines=1)
                all_rentals_df_display = gr.DataFrame(
                    label="전체 대여 현황 목록",
                    headers=["대여자 (Borrower)", "장비명 (Equipment Name)", "수량 (Quantity)", "대여 시작일 (Start Date)", "반납 기한 (End Date)", "상태 (Status)"],
                    datatype=['str', 'str', 'number', 'date', 'date', 'str'], # Adjust datatypes as needed
                    row_count=(10, "dynamic"),
                    col_count=(6, "fixed"), # 6 columns now
                    interactive=False # Typically display-only
                )

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
                        admin_equipments_df_display = gr.DataFrame(label="시스템 등록 장비 목록", headers=['ID', '장비명', '부서', '총량', '가용량'], value=pd.DataFrame(columns=['ID', '장비명', '부서', '총량', '가용량']), datatype=['str', 'str', 'str', 'number', 'number'], interactive=True, row_count=(10, "dynamic"), col_count=(5,"fixed"))
                    with gr.TabItem("➕➖ 장비 추가/수정", id="admin_add_edit_tab"):
                        gr.Markdown("### 장비 정보 입력/수정 (목록에서 선택 시 자동 입력)")
                        admin_edit_id_input = gr.Textbox(label="장비 ID (필수, 고유값)", placeholder="예: EQP-XYZ-001")
                        admin_edit_name_input = gr.Textbox(label="장비명 (필수)", placeholder="예: 고성능 오실로스코프")
                        admin_edit_dept_dropdown = gr.Dropdown(label="부서 (필수)", choices=["물리과", "화학과", "IT과", "공과대학", "공용"], value="공용")
                        admin_edit_qty_input = gr.Textbox(label="총 수량 (필수, 숫자)", placeholder="예: 5")
                        with gr.Row(): admin_add_button = gr.Button("➕ 새 장비 추가", variant="primary"); admin_update_button = gr.Button("💾 선택 장비 정보 수정", variant="secondary"); admin_clear_fields_button = gr.Button("✨ 입력 초기화")
                gr.Markdown("---"); logout_button_admin_tab = gr.Button("🔒 관리자 로그아웃"); logout_status_admin_tab_output = gr.Textbox(label="로그아웃 상태", interactive=False)

            # --- Search Tab Event Handlers ---
            # Simple passthrough to update current_search_df_state, can remain lambda or be extracted if more logic added later.
            search_results_df.change(lambda x: x, inputs=[search_results_df], outputs=[current_search_df_state])
            search_button.click(fetch_equipments, inputs=[search_dept_dropdown, search_term_input], outputs=[search_results_df, search_status_output])
            search_results_df.select(df_select_for_rental, inputs=[current_search_df_state], outputs=[selected_items_display, selected_equipment_to_rent_var, request_rental_button])
            request_rental_button.click(handle_request_rental_navigation, inputs=[selected_equipment_to_rent_var, user_session_var, main_tabs], outputs=[main_tabs])

            show_all_rentals_button.click(
                handle_fetch_all_rentals_ui,
                inputs=None,
                outputs=[all_rentals_df_state, all_rentals_status_output]
            )
            all_rentals_df_state.change(
                lambda x: x,
                inputs=[all_rentals_df_state],
                outputs=[all_rentals_df_display]
            )

            # --- Rental Tab Event Handlers ---
            selected_equipment_to_rent_var.change(update_rental_selected_display, inputs=[selected_equipment_to_rent_var], outputs=[rental_selected_display])
            confirm_rental_button.click(process_rental_request, inputs=[selected_equipment_to_rent_var, rental_start_date_input, rental_end_date_input, rental_borrower_name_input, rental_purpose_input, user_session_var], outputs=[rental_status_output, selected_equipment_to_rent_var])

            # --- Admin Tab Event Handlers ---
            admin_refresh_equip_list_button.click(handle_fetch_all_equip_admin, inputs=[user_session_var], outputs=[admin_all_equipments_df_state, admin_status_output])
            # Simple passthrough, can remain lambda
            admin_all_equipments_df_state.change(lambda df_data: df_data, inputs=[admin_all_equipments_df_state], outputs=[admin_equipments_df_display])
            admin_equipments_df_display.select(admin_df_select_for_edit, inputs=[admin_all_equipments_df_state], outputs=[selected_equipment_for_edit_state, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, admin_sub_tabs])
            admin_add_button.click(add_equip_refresh_list, inputs=[admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, user_session_var, admin_all_equipments_df_state], outputs=[admin_status_output, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, admin_all_equipments_df_state])
            admin_update_button.click(update_equip_refresh_list, inputs=[selected_equipment_for_edit_state, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, user_session_var, admin_all_equipments_df_state], outputs=[admin_status_output, selected_equipment_for_edit_state, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, admin_all_equipments_df_state])
            admin_clear_fields_button.click(clear_admin_form_fields_action, outputs=[selected_equipment_for_edit_state, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, admin_status_output])

            # --- Auth Event Handlers ---
            signup_button.click(handle_signup_action, inputs=[signup_email_input, signup_password_input, signup_confirm_password_input], outputs=[signup_status_output])
            login_button.click(handle_login_ui_updates, inputs=[login_email_input, login_password_input, admin_all_equipments_df_state, main_tabs], outputs=[login_status_output, user_session_var, auth_forms_group, user_info_group, auth_tab_item_obj, admin_management_tab_item_obj, main_tabs, admin_all_equipments_df_state, admin_status_output])
            logout_button_auth_tab.click(universal_logout_ui_updates, inputs=[user_session_var], outputs=[logout_status_auth_tab_output, user_session_var, auth_forms_group, user_info_group, auth_tab_item_obj, admin_management_tab_item_obj, main_tabs, selected_equipment_to_rent_var, admin_all_equipments_df_state, selected_equipment_for_edit_state, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, admin_status_output])
            logout_button_admin_tab.click(universal_logout_ui_updates, inputs=[user_session_var], outputs=[logout_status_admin_tab_output, user_session_var, auth_forms_group, user_info_group, auth_tab_item_obj, admin_management_tab_item_obj, main_tabs, selected_equipment_to_rent_var, admin_all_equipments_df_state, selected_equipment_for_edit_state, admin_edit_id_input, admin_edit_name_input, admin_edit_dept_dropdown, admin_edit_qty_input, admin_status_output])
            user_session_var.change(update_user_display, inputs=[user_session_var], outputs=[current_user_display])

        demo.launch(debug=True, share=False)
        print("Gradio app launched with full Admin Management Tab.")

# Read app.py
with open("app.py", "r") as f:
    content = f.read()

# Modify login_button.click inputs
# Original: inputs=[login_email_input, login_password_input, admin_all_equipments_df_state, main_tabs]
# New:      inputs=[login_email_input, login_password_input, admin_all_equipments_df_state]
content = content.replace(
    "login_button.click(handle_login_ui_updates, inputs=[login_email_input, login_password_input, admin_all_equipments_df_state, main_tabs]",
    "login_button.click(handle_login_ui_updates, inputs=[login_email_input, login_password_input, admin_all_equipments_df_state]"
)

# Modify handle_login_ui_updates function definition
# Original: def handle_login_ui_updates(email: str, pw: str, current_admin_df: pd.DataFrame, current_main_tabs: gr.Tabs) -> tuple:
# New:      def handle_login_ui_updates(email: str, pw: str, current_admin_df: pd.DataFrame) -> tuple:
content = content.replace(
    "def handle_login_ui_updates(email: str, pw: str, current_admin_df: pd.DataFrame, current_main_tabs: gr.Tabs) -> tuple:",
    "def handle_login_ui_updates(email: str, pw: str, current_admin_df: pd.DataFrame) -> tuple:"
)

# Modify the return statement in the else block of handle_login_ui_updates for main_tabs output
# Original line (part of a tuple): current_main_tabs,
# We need to find the specific return tuple for the failure case.
# It looks like:
# return msg, None, gr.update(visible=True), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), current_main_tabs, current_admin_df, ""
# The 7th element is current_main_tabs. It should become gr.update()
# This is fragile if the number of returned elements changes. A more robust way would be to parse the AST or use regex with care.
# For now, using a targeted string replacement that assumes the structure.

# Let's try a more specific replacement for the return tuple in the else block
original_failure_return_tuple = 'msg, None, gr.update(visible=True), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), current_main_tabs, current_admin_df, ""'
new_failure_return_tuple = 'msg, None, gr.update(visible=True), gr.update(visible=False), gr.update(visible=True), gr.update(visible=False), gr.update(), current_admin_df, ""'

content = content.replace(original_failure_return_tuple, new_failure_return_tuple)

# Write the modified content back to app.py
with open("app.py", "w") as f:
    f.write(content)

print("app.py modified to fix InvalidComponentError for login button.")
# Verify the changes by printing relevant snippets
print("\n--- Verifying login_button.click ---")
with open("app.py", "r") as f:
    for line in f:
        if "login_button.click" in line:
            print(line.strip())
            break # Show first occurrence

print("\n--- Verifying handle_login_ui_updates definition ---")
with open("app.py", "r") as f:
    for line in f:
        if "def handle_login_ui_updates" in line:
            print(line.strip())
            break

print("\n--- Verifying handle_login_ui_updates failure return ---")
# This is harder to grep simply, but the change should be applied.
# We can search for the new tuple structure.
with open("app.py", "r") as f:
    for line in f:
        if new_failure_return_tuple in line:
            print("Found new failure return tuple snippet:")
            print(line.strip())
            break
    else: # If loop finishes without break
        print("Could not find the new failure return tuple snippet. Manual check might be needed or original was slightly different.")
        print("Searching for parts of it:")
        with open("app.py", "r") as f_recheck:
            for line_recheck in f_recheck:
                if "gr.update(), current_admin_df," in line_recheck:
                    print("Found partial match for new failure return:")
                    print(line_recheck.strip())
                    break

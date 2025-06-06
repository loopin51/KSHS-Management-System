import re
from supabase import Client # For type hinting Session, User
from typing import Optional, Tuple, Any # For type hinting

# ADMIN_EMAIL will be passed as an argument where needed

def is_valid_email(email: str) -> bool:
    if not email: return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

def signup_user(supabase: Client, email: str, password: str, confirm_password: str) -> str:
    if not supabase: return "Supabase client not initialized."
    if not is_valid_email(email): return "Invalid email format."
    if not password: return "Password cannot be empty."
    if password != confirm_password: return "Passwords do not match."
    if len(password) < 6: return "Password must be at least 6 characters long."
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        # Correctly check for user and session attributes based on Supabase response structure
        if hasattr(res, 'user') and res.user and hasattr(res.user, 'aud') and res.user.aud == 'authenticated':
            # Check if session is None, which might indicate email confirmation is needed
            if not hasattr(res, 'session') or not res.session:
                 return f"Signup successful for {email}! Check email to confirm."
            return f"Signup successful! Welcome {res.user.email}."
        elif hasattr(res, 'error') and res.error:
            return f"Signup failed: {res.error.message}"
        else:
            # Attempt to sign in to check if user is already confirmed
            try:
                sign_in_res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if hasattr(sign_in_res, 'user') and sign_in_res.user:
                    return "This email is already registered and confirmed. Please log in."
            except Exception: # Catch sign-in errors if user exists but password is wrong, etc.
                pass # Don't obscure original signup issue
            return "Signup failed. The email might already be in use or an issue occurred."
    except Exception as e:
        # Check for specific error messages from Supabase
        if "User already registered" in str(e) or (hasattr(e, 'message') and "User already exists" in str(e.message)):
            return "User already registered. Please log in or check your email for confirmation."
        return f"An unexpected error occurred during signup: {str(e)}"

def login_user(supabase: Client, email: str, password: str) -> Tuple[Optional[Any], str]: # Return type uses Any for session
    if not supabase: return None, "Supabase client not initialized."
    if not is_valid_email(email): return None, "Invalid email format."
    if not password: return None, "Password cannot be empty."
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if hasattr(res, 'user') and res.user and hasattr(res, 'session') and res.session:
            print(f"User {res.user.email} logged in.")
            return res.session, f"Login successful! Welcome {res.user.email}."
        elif hasattr(res, 'error') and res.error:
            return None, f"Login failed: {res.error.message}"
        else:
            return None, "Login failed. Check credentials or confirm email."
    except Exception as e:
        return None, f"An unexpected error during login: {str(e)}"

def logout_user(supabase: Client, session_state: Optional[Any]) -> Tuple[str, Optional[Any], list]: # Return type uses Any for session
    if not supabase: return "Supabase client not initialized.", session_state, []
    if session_state and hasattr(session_state, 'user') and session_state.user:
        try:
            supabase.auth.sign_out()
            print("User logged out from Supabase.")
            return "Logout successful.", None, []
        except Exception as e:
            print(f"Error during Supabase sign_out: {str(e)}")
            return f"Logout error: {str(e)}", None, [] # Session should be None even if error on Supabase side
    return "No active session.", session_state, []

def get_user_role(user_session: Optional[Any], admin_email: Optional[str]) -> Optional[str]: # Return type uses Any for session
    if user_session and hasattr(user_session, 'user') and user_session.user and hasattr(user_session.user, 'email'):
        if admin_email and user_session.user.email == admin_email:
            return 'admin'
        return 'user'
    return None

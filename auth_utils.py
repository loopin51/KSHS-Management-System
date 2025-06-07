import re

def is_valid_email(email: str) -> bool:
    """
    Validates an email address using a regex pattern.
    """
    if not email:
        return False
    # Regex pattern from the previous task, modified to disallow consecutive dots in domain
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

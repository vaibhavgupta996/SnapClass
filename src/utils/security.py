import re

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validates password strength criteria:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    - At least 1 special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must include at least one uppercase letter (A-Z)."
    if not re.search(r"[a-z]", password):
        return False, "Password must include at least one lowercase letter (a-z)."
    if not re.search(r"\d", password):
        return False, "Password must include at least one digit (0-9)."
    if not re.search(r"[@$!%*?&#^+=~._-]", password):
        return False, "Password must include at least one special character (@$!%*?&#^+=~._-)."
    
    return True, "Strong Password"
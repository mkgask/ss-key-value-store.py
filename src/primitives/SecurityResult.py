from enum import Enum

class SecurityResult(Enum):
    """
    Enum-like class to represent different security result states.
    """
    ALLOWED = "allowed"
    DENIED = "denied"
    RATE_LIMITED = "rate_limited"
    INVALID_TOKEN = "invalid_token"
    INVALID_PERMISSIONS = "invalid_permissions"
    UNAUTHORIZED_PATH = "unauthorized_path"

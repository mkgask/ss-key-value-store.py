from enum import Enum

class AccessLevel(Enum):
    """
    Enum-like class to represent different access levels.
    """
    ADMIN = "admin"
    READ_WRITE = "read_write"
    WRITE_ONLY = "write_only"
    READ_ONLY = "read_only"

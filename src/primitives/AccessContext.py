from dataclasses import dataclass, field
from typing import Any, Optional
import time

@dataclass
class AccessContext:
    """
    A class to represent the context of an access request.
    """
    name: str
    key: str
    operation: str
    caller: str
    value: Optional[Any] = None
    timestamp: str = field(default_factory=lambda: time.time)

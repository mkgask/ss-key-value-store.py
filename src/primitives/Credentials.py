from dataclasses import dataclass, field
import time
from typing import Optional

from .AccessLevel import AccessLevel

@dataclass(frozen=True)
class Credentials:
    """
    A class to represent credentials.
    frozen=True により、作成後のフィールド変更を防止
    """
    name: str
    key: str
    access_level: AccessLevel
    path: str = ""
    type: str = ""
    enabled: bool = False
    created_at: float = field(default_factory=time.time)
    last_access: float = field(default_factory=time.time)
    access_count: int = 0
    
    def with_updated_access(self, last_access: Optional[float] = None, access_count: Optional[int] = None) -> 'Credentials':
        """
        アクセス情報を更新した新しいCredentialsインスタンスを返却
        immutableパターンの実装
        """
        return Credentials(
            name=self.name,
            key=self.key,
            access_level=self.access_level,
            path=self.path,
            type=self.type,
            enabled=True,
            created_at=self.created_at,
            last_access=last_access or time.time(),
            access_count=access_count or (self.access_count + 1)
        )

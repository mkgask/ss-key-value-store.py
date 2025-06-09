import secrets
import time
from typing import Optional, List, Callable, Union

from ..foundation.ProtectedStore import ProtectedStore
from ..foundation.PathResolver import PathResolver
from ..primitives.PathInfo import PathInfo 
from ..primitives.AccessLevel import AccessLevel
from ..primitives.AccessOperation import AccessOperation
from ..primitives.Credentials import Credentials

"""
CredentialManager is responsible for managing credentials, including registration, validation, and access control.
It provides methods to register new credentials, validate existing ones, and manage access levels.
It uses a PathResolver to determine the context of the operation and ensures that credentials are managed securely.
"""
class CredentialManager:
    __slots__ = ['_credentials', 'path_resolver', '_register_callbacks']
    
    def __init__(self, credentials_roots: Union[str, List[str]]):
        """
        CredentialManagerの初期化
        credentials_rootsには単一のパスまたは複数のベースパスを指定可能
        """
        self._credentials = ProtectedStore(allowed_accessor=self)
        self.path_resolver = PathResolver(credentials_roots)
        self._register_callbacks: List[Callable[[Credentials], None]] = []
    
    def get_credential_count(self) -> int:
        """
        登録済み認証情報の数を取得（安全なアクセス方法）
        """
        return len(self._credentials)
    
    def has_credential(self, caller_name: str) -> bool:
        """
        指定した呼び出し元の認証情報が存在するかチェック
        """
        return caller_name in self._credentials

    def setRegisterCallback(self, callback: Callable[[Credentials], None]) -> None:
        """
        認証情報登録時に実行されるコールバックを設定
        """
        if callback not in self._register_callbacks:
            self._register_callbacks.append(callback)

    def register(self, access_level: AccessLevel = AccessLevel.READ_ONLY) -> Credentials:
        """
        Register a new credential.
        """
        pathinfo = self.path_resolver.getPathInfo()
        caller = pathinfo.name

        # 管理者権限の登録時は昇格可能性をチェック
        if access_level == AccessLevel.ADMIN and not self.canEscalateToAdmin(pathinfo):
            raise ValueError(f"Admin access level is not allowed for caller: {caller}")

        key = f"{caller}_{secrets.token_urlsafe(16)}"

        credential = Credentials(
            name = caller,
            key = key,
            access_level = access_level,
            path = pathinfo.path,
            type = pathinfo.type,
        )

        self._credentials[caller] = credential

        # 登録コールバックの実行
        for callback in self._register_callbacks:
            try:
                callback(credential)
            except Exception as e:
                # コールバック実行エラーは記録するが、登録処理は継続
                print(f"Warning: Register callback failed: {e}")

        return credential

    def canEscalateToAdmin(self, pathinfo: PathInfo) -> bool:
        """
        Check if the caller can escalate to admin level.
        Returns False if the caller path contains 'plugin' keyword.
        """
        if "plugin" in pathinfo.type or "unknown" in pathinfo.type:
            return False

        return True

    def validate(self, operation: AccessOperation) -> bool:
        try:
            credendial = self.getCredential(operation)
            return credendial.enabled
        except ValueError:
            return False

    def getKey(self) -> str:
        """
        Get the key of the credential based on the caller's path info.
        Returns None if no valid credential is found.
        """
        pathinfo = self.path_resolver.getPathInfo()
        caller = pathinfo.name

        for credential in self._credentials.values():
            if credential.name == caller:
                return credential.key

        raise ValueError(f"No valid credential found for caller: {caller}")

    def getCredential(self, operation: AccessOperation) -> Credentials:
        """
        Validate a credential by its key.
        """
        pathinfo = self.path_resolver.getPathInfo()
        caller = pathinfo.name

        for credential in self._credentials.values():
            if not credential.name == caller:
                continue

            if credential.access_level == AccessLevel.ADMIN:
                return self._enableCredentials(credential)
            elif credential.access_level == AccessLevel.READ_WRITE and operation in [AccessOperation.READ, AccessOperation.WRITE]:
                return self._enableCredentials(credential)
            elif credential.access_level == AccessLevel.WRITE_ONLY and operation == AccessOperation.WRITE:
                return self._enableCredentials(credential)
            elif credential.access_level == AccessLevel.READ_ONLY and operation == AccessOperation.READ:
                return self._enableCredentials(credential)

        raise ValueError(f"Invalid credential: {caller} for operation: {operation}")

    def _enableCredentials(self, credential: Credentials) -> Credentials:
        # immutableパターンで新しいCredentialsインスタンスを生成
        enabled_credential = credential.with_updated_access()

        # 内部ストレージの更新（統計情報のみ）
        if credential.name in self._credentials:
            self._credentials[credential.name] = credential.with_updated_access(
                last_access=enabled_credential.last_access,
                access_count=enabled_credential.access_count
            )

        return enabled_credential

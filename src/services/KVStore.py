from typing import Dict, Any

from .CredentialManager import CredentialManager
from ..foundation.ProtectedStore import ProtectedStore
from ..primitives.AccessOperation import AccessOperation
from ..primitives.AccessLevel import AccessLevel
from ..primitives.Credentials import Credentials

class KVStore:
    def __init__(self, credentials_manager: CredentialManager) -> None:
        self._credentials_manager = credentials_manager

        # 呼び出し元別ストレージの登録簿もProtectedStoreで保護
        self._caller_storages: ProtectedStore = ProtectedStore(
            allowed_accessor=KVStore
        )

        # 共通読み書きストレージ（全員がアクセス可能）
        self._shared_read_write_store: ProtectedStore = ProtectedStore(
            allowed_accessor=KVStore
        )

        # 共通読み込み専用ストレージ（一般ユーザーは読み取り専用、管理者のみ書き込み可能）
        self._shared_read_only_store: ProtectedStore = ProtectedStore(
            allowed_accessor=KVStore
        )

        # 認証情報登録時のコールバックを設定
        self._credentials_manager.setRegisterCallback(self._on_credential_registered)

    def _on_credential_registered(self, credential: Credentials) -> None:
        """
        認証情報が登録された際に実行されるコールバック
        呼び出し元専用のProtectedStoreを自動生成
        """
        caller_storage = ProtectedStore(allowed_accessor=KVStore)
        self._caller_storages.set(credential.name, caller_storage)

    def _get_caller_storage(self) -> ProtectedStore:
        """
        現在の呼び出し元用のストレージを取得
        """
        pathinfo = self._credentials_manager.path_resolver.getPathInfo()
        caller_name = pathinfo.name
        
        storage = self._caller_storages.get(caller_name)
        if storage is None:
            raise ValueError(f"No storage found for caller: {caller_name}")
        
        return storage

    def set(self, key: str, value: str) -> None:
        self._credentials_manager.validate(AccessOperation.WRITE)
        caller_storage = self._get_caller_storage()
        caller_storage.set(key, value)

    def get(self, key: str, default: Any = None) -> Any:
        self._credentials_manager.validate(AccessOperation.READ)
        caller_storage = self._get_caller_storage()
        return caller_storage.get(key, default)

    def has(self, key: str) -> bool:
        self._credentials_manager.validate(AccessOperation.READ)
        caller_storage = self._get_caller_storage()
        return key in caller_storage
    
    def delete(self, key: str) -> None:
        self._credentials_manager.validate(AccessOperation.WRITE)
        caller_storage = self._get_caller_storage()

        if key in caller_storage:
            del caller_storage[key]

    def clear(self) -> None:
        self._credentials_manager.validate(AccessOperation.WRITE)
        caller_storage = self._get_caller_storage()
        caller_storage.clear()

    def keys(self) -> Dict[str, Any]:
        self._credentials_manager.validate(AccessOperation.READ)
        caller_storage = self._get_caller_storage()
        return caller_storage.keys()

    def values(self) -> Dict[str, Any]:
        self._credentials_manager.validate(AccessOperation.READ)
        caller_storage = self._get_caller_storage()
        return caller_storage.values()

    def _is_admin_user(self) -> bool:
        """
        現在の呼び出し元が管理者権限を持っているかチェック
        """
        try:
            # 管理者権限での認証情報取得を試行
            credential = self._credentials_manager.getCredential(AccessOperation.WRITE)
            return credential.access_level == AccessLevel.ADMIN
        except ValueError:
            return False

    # 共通読み書きストレージのメソッド
    def shared_set(self, key: str, value: str) -> None:
        """
        共通読み書きストレージにキーと値を設定
        全ユーザーが書き込み可能
        """
        self._credentials_manager.validate(AccessOperation.WRITE)
        self._shared_read_write_store.set(key, value)

    def shared_get(self, key: str, default: Any = None) -> Any:
        """
        共通読み書きストレージから値を取得
        全ユーザーが読み取り可能
        """
        self._credentials_manager.validate(AccessOperation.READ)
        return self._shared_read_write_store.get(key, default)

    def shared_has(self, key: str) -> bool:
        """
        共通読み書きストレージにキーが存在するかチェック
        """
        self._credentials_manager.validate(AccessOperation.READ)
        return key in self._shared_read_write_store

    def shared_delete(self, key: str) -> None:
        """
        共通読み書きストレージからキーを削除
        全ユーザーが削除可能
        """
        self._credentials_manager.validate(AccessOperation.WRITE)
        if key in self._shared_read_write_store:
            del self._shared_read_write_store[key]

    def shared_clear(self) -> None:
        """
        共通読み書きストレージをクリア
        全ユーザーがクリア可能
        """
        self._credentials_manager.validate(AccessOperation.WRITE)
        self._shared_read_write_store.clear()

    def shared_keys(self) -> Dict[str, Any]:
        """
        共通読み書きストレージのキー一覧を取得
        """
        self._credentials_manager.validate(AccessOperation.READ)
        return self._shared_read_write_store.keys()

    def shared_values(self) -> Dict[str, Any]:
        """
        共通読み書きストレージの値一覧を取得
        """
        self._credentials_manager.validate(AccessOperation.READ)
        return self._shared_read_write_store.values()

    # 共通読み込み専用ストレージのメソッド
    def readonly_set(self, key: str, value: str) -> None:
        """
        共通読み込み専用ストレージにキーと値を設定
        管理者のみ書き込み可能
        """
        self._credentials_manager.validate(AccessOperation.WRITE)
        if not self._is_admin_user():
            raise PermissionError("Admin access required for write operations on read-only storage")
        self._shared_read_only_store.set(key, value)

    def readonly_get(self, key: str, default: Any = None) -> Any:
        """
        共通読み込み専用ストレージから値を取得
        全ユーザーが読み取り可能
        """
        self._credentials_manager.validate(AccessOperation.READ)
        return self._shared_read_only_store.get(key, default)

    def readonly_has(self, key: str) -> bool:
        """
        共通読み込み専用ストレージにキーが存在するかチェック
        """
        self._credentials_manager.validate(AccessOperation.READ)
        return key in self._shared_read_only_store

    def readonly_delete(self, key: str) -> None:
        """
        共通読み込み専用ストレージからキーを削除
        管理者のみ削除可能
        """
        self._credentials_manager.validate(AccessOperation.WRITE)
        if not self._is_admin_user():
            raise PermissionError("Admin access required for delete operations on read-only storage")
        if key in self._shared_read_only_store:
            del self._shared_read_only_store[key]

    def readonly_clear(self) -> None:
        """
        共通読み込み専用ストレージをクリア
        管理者のみクリア可能
        """
        self._credentials_manager.validate(AccessOperation.WRITE)
        if not self._is_admin_user():
            raise PermissionError("Admin access required for clear operations on read-only storage")
        self._shared_read_only_store.clear()

    def readonly_keys(self) -> Dict[str, Any]:
        """
        共通読み込み専用ストレージのキー一覧を取得
        """
        self._credentials_manager.validate(AccessOperation.READ)
        return self._shared_read_only_store.keys()

    def readonly_values(self) -> Dict[str, Any]:
        """
        共通読み込み専用ストレージの値一覧を取得
        """
        self._credentials_manager.validate(AccessOperation.READ)
        return self._shared_read_only_store.values()

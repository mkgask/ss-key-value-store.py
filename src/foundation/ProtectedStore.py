from typing import Dict, Any, Union, Type, Callable

import inspect
import copy

class ProtectedStore:
    """
    A class to manage a protected store with a dictionary.
    """

    def __init__(self, allowed_accessor: Union[object, Type, str, Callable[[object], bool]] = None):
        """
        Initialize the ProtectedStore with flexible access control.
        
        Args:
            allowed_accessor: 以下のいずれかを指定可能:
                - object: 特定のインスタンスのみ許可（従来の動作）
                - Type: 指定されたクラスのインスタンスを許可
                - str: 指定されたクラス名のインスタンスを許可
                - Callable: カスタム検証関数（caller_self -> bool）
        """
        if allowed_accessor is None:
            raise ValueError("An allowed accessor must be provided.")

        self._store: Dict[str, Any] = {}
        self._allowed_accessor = allowed_accessor

    def _is_access_allowed(self, caller_self: object) -> bool:
        """
        許可されたアクセサーかどうかを柔軟にチェックする。
        
        Args:
            caller_self: チェック対象のself参照
            
        Returns:
            bool: アクセスが許可されている場合True
        """
        if caller_self is None:
            return False
            
        # インスタンス同一性チェック（従来の動作）
        if isinstance(self._allowed_accessor, object) and not isinstance(self._allowed_accessor, (type, str)) and not callable(self._allowed_accessor):
            return caller_self is self._allowed_accessor
        
        # クラス型チェック
        if isinstance(self._allowed_accessor, type):
            return isinstance(caller_self, self._allowed_accessor)
        
        # クラス名文字列チェック
        if isinstance(self._allowed_accessor, str):
            try:
                return caller_self.__class__.__name__ == self._allowed_accessor
            except AttributeError:
                return False
        
        # カスタム検証関数
        if callable(self._allowed_accessor):
            try:
                return self._allowed_accessor(caller_self)
            except Exception:
                return False
        
        return False

    def _check_access_allowed(self) -> None:
        """
        Check if the method is allowed to be accessed.
        Raises PermissionError if the method is not allowed.
        
        セキュリティを保ちながら、限定的なフレームチェーンチェックを行う。
        最大2フレームまでのみ検索し、許可されたアクセサーからの呼び出しかチェックする。
        """
        current_frame = inspect.currentframe()

        try:
            # current_frame が None の場合のハンドリング
            if current_frame is None:
                raise RuntimeError("No current frame found.")
            
            # 呼び出し元フレームがない場合のハンドリング
            if current_frame.f_back is None:
                raise RuntimeError("No caller frame found.")
            
            # 限定的なフレームチェーン検索（最大3フレームまで）
            frames_to_check = []
            frame = current_frame.f_back
            max_frames = 3  # セキュリティのため、検索は最大3フレームまでに制限
            
            for _ in range(max_frames):
                if frame is None:
                    break

                frames_to_check.append(frame)
                frame = frame.f_back
            
            # いずれかのフレームに許可されたアクセサーがあるかチェック
            for i, frame_to_check in enumerate(frames_to_check):
                caller_self = frame_to_check.f_locals.get('self')
                
                if self._is_access_allowed(caller_self):
                    return  # 許可されたアクセス
            
            # どのフレームでも許可されたアクセサーが見つからない場合はエラー
            # デバッグ情報生成を簡素化（無限ループ回避）
            try:
                if isinstance(self._allowed_accessor, type):
                    expected_type = self._allowed_accessor.__name__
                elif isinstance(self._allowed_accessor, str):
                    expected_type = self._allowed_accessor
                elif hasattr(self._allowed_accessor, '__class__'):
                    expected_type = self._allowed_accessor.__class__.__name__
                else:
                    expected_type = 'Custom_Function'
            except:
                expected_type = 'Unknown'
            
            # 簡素化されたエラーメッセージ（文字列操作を最小限に）
            raise PermissionError(
                f"Access only allowed from authorized accessor. Expected: {expected_type}"
            )
                
        finally:
            del current_frame

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set an item in the store.
        """
        self.set(key, value)

    def __getitem__(self, key: str) -> Any:
        """
        Get an item from the store.
        """
        self._check_access_allowed()
        return self._store[key]
    
    def __delitem__(self, key: str) -> None:
        """
        Delete an item from the store.
        """
        self._check_access_allowed()
        del self._store[key]

    def __contains__(self, key: str) -> bool:
        """
        Check if an item exists in the store.
        """
        self._check_access_allowed()
        return key in self._store
    
    def __len__(self) -> int:
        """
        Get the number of items in the store.
        """
        self._check_access_allowed()
        return len(self._store)
    
    def clear(self) -> None:
        """
        Clear the store.
        """
        self._check_access_allowed()
        self._store.clear()

    def items(self):
        """
        Get all items in the store.
        """
        self._check_access_allowed()
        return self._store.items()
    
    def keys(self):
        """
        Get all keys in the store.
        """
        self._check_access_allowed()
        return self._store.keys()
    
    def values(self):
        """
        Get all values in the store.
        """
        self._check_access_allowed()
        return self._store.values()
    
    def get(self, key: str, default=None) -> Any:
        """
        Get an item from the store with a default value.
        """
        self._check_access_allowed()
        return self._store.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set an item in the store.
        """
        self._check_access_allowed()
        self._store[key] = value

    def deep_copy(self) -> Dict[str, Any]:
        """
        Return a deep copy of the store.
        """
        self._check_access_allowed()
        return copy.deepcopy(self._store)

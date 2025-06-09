import sys
import os
import tempfile
import shutil
from unittest.mock import patch


# テスト対象クラスのインポート
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try:
    from src.services.KVStore import KVStore
    from src.services.CredentialManager import CredentialManager
    from src.primitives.AccessLevel import AccessLevel
    from src.primitives.PathInfo import PathInfo
except ImportError as e:
    print(f"インポートエラーが発生しました: {e}")
    sys.exit(1)



class TestKVStoreBasicFunctionality:
    """
    KVStoreの基本機能をテストするクラス
    """

    def setup_method(self):
        """
        各テストメソッドの実行前に呼び出されるセットアップメソッド
        テスト用のCredentialManagerとKVStoreインスタンスを作成
        """
        self.temp_dir = tempfile.mkdtemp()
        self.credential_manager = CredentialManager(self.temp_dir)
        self.kvstore = KVStore(self.credential_manager)
        
        # テスト用の認証情報を登録
        self.mock_path_info = PathInfo(
            name="test_user",
            path="/path/to/test_user/module.py",
            type="test_services"
        )
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            self.credential_manager.register(AccessLevel.READ_WRITE)

    def teardown_method(self):
        """
        各テストメソッド実行後のクリーンアップ処理
        """
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_kvstore_initialization_creates_instance_successfully(self):
        """
        KVStoreが正常にインスタンス化されることを確認
        """
        assert self.kvstore is not None
        assert self.kvstore._credentials_manager is self.credential_manager

    def test_set_and_get_single_key_value_pair(self):
        """
        単一のキー・バリューペアの設定と取得が正常に動作することを確認
        """
        test_key = "test_key"
        test_value = "test_value"
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            self.kvstore.set(test_key, test_value)
            retrieved_value = self.kvstore.get(test_key)
        
        assert retrieved_value == test_value

    def test_get_nonexistent_key_returns_none_by_default(self):
        """
        存在しないキーを取得した場合にNoneが返されることを確認
        """
        nonexistent_key = "nonexistent_key"
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            result = self.kvstore.get(nonexistent_key)
        
        assert result is None

    def test_get_nonexistent_key_returns_specified_default_value(self):
        """
        存在しないキーを取得した場合に指定されたデフォルト値が返されることを確認
        """
        nonexistent_key = "nonexistent_key"
        default_value = "default_value"
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            result = self.kvstore.get(nonexistent_key, default_value)
        
        assert result == default_value

    def test_has_returns_true_for_existing_key(self):
        """
        存在するキーに対してhas()がTrueを返すことを確認
        """
        test_key = "existing_key"
        test_value = "existing_value"
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            self.kvstore.set(test_key, test_value)
            assert self.kvstore.has(test_key) is True

    def test_has_returns_false_for_nonexistent_key(self):
        """
        存在しないキーに対してhas()がFalseを返すことを確認
        """
        nonexistent_key = "nonexistent_key"
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            assert self.kvstore.has(nonexistent_key) is False

    def test_delete_existing_key_removes_key_successfully(self):
        """
        既存のキーを削除すると正常に削除されることを確認
        """
        test_key = "key_to_delete"
        test_value = "value_to_delete"
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            self.kvstore.set(test_key, test_value)
            assert self.kvstore.has(test_key) is True
            
            self.kvstore.delete(test_key)
            assert self.kvstore.has(test_key) is False

    def test_delete_nonexistent_key_does_not_raise_error(self):
        """
        存在しないキーを削除してもエラーが発生しないことを確認
        """
        nonexistent_key = "nonexistent_key"
        
        # エラーが発生せずに正常に実行されることを確認
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            self.kvstore.delete(nonexistent_key)

    def test_clear_removes_all_stored_data(self):
        """
        clear()メソッドがすべての格納データを削除することを確認
        """
        # 複数のキー・バリューペアを設定
        test_data = {
            "key1": "value1",
            "key2": "value2", 
            "key3": "value3"
        }
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            for key, value in test_data.items():
                self.kvstore.set(key, value)
            
            # すべてのキーが存在することを確認
            for key in test_data.keys():
                assert self.kvstore.has(key) is True
            
            # clear実行
            self.kvstore.clear()
            
            # すべてのキーが削除されていることを確認
            for key in test_data.keys():
                assert self.kvstore.has(key) is False

    def test_keys_returns_all_stored_keys(self):
        """
        keys()メソッドがすべての格納されたキーを返すことを確認
        """
        test_data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            for key, value in test_data.items():
                self.kvstore.set(key, value)
            
            returned_keys = self.kvstore.keys()
        
        # 返されたキーが期待されるキーと一致することを確認
        assert set(returned_keys) == set(test_data.keys())

    def test_values_returns_all_stored_values(self):
        """
        values()メソッドがすべての格納された値を返すことを確認
        """
        test_data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            for key, value in test_data.items():
                self.kvstore.set(key, value)
            
            returned_values = self.kvstore.values()
        
        # 返された値が期待される値と一致することを確認
        assert set(returned_values) == set(test_data.values())

    def test_overwrite_existing_key_updates_value(self):
        """
        既存のキーに新しい値を設定すると値が更新されることを確認
        """
        test_key = "overwrite_key"
        original_value = "original_value"
        new_value = "new_value"
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            # 初期値を設定
            self.kvstore.set(test_key, original_value)
            assert self.kvstore.get(test_key) == original_value
            
            # 新しい値で上書き
            self.kvstore.set(test_key, new_value)
            assert self.kvstore.get(test_key) == new_value

    def test_multiple_operations_maintain_data_integrity(self):
        """
        複数の操作を組み合わせてもデータの整合性が保たれることを確認
        """
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.mock_path_info):
            # 複数のキー・バリューペアを設定
            self.kvstore.set("key1", "value1")
            self.kvstore.set("key2", "value2")
            self.kvstore.set("key3", "value3")
            
            # 一部のキーを削除
            self.kvstore.delete("key2")
            
            # 新しいキーを追加
            self.kvstore.set("key4", "value4")
            
            # 既存のキーを上書き
            self.kvstore.set("key1", "updated_value1")
            
            # 期待される状態を確認
            assert self.kvstore.has("key1") is True
            assert self.kvstore.get("key1") == "updated_value1"
            assert self.kvstore.has("key2") is False
            assert self.kvstore.has("key3") is True
            assert self.kvstore.get("key3") == "value3"
            assert self.kvstore.has("key4") is True
            assert self.kvstore.get("key4") == "value4"

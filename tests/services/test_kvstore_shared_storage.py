#!/usr/bin/env python3
"""
KVStoreクラスの共通ストレージ機能テストモジュール

このテストモジュールは新たに追加された共通ストレージ機能をテストします：
- 共通読み書きストレージの機能検証
- 共通読み込み専用ストレージの機能検証
- 管理者権限によるアクセス制御の検証
- ストレージ間の分離性の確認
"""

import sys
import os
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# テスト対象クラスのインポート
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try:
    from src.services.KVStore import KVStore
    from src.services.CredentialManager import CredentialManager
    from src.primitives.AccessLevel import AccessLevel
    from src.primitives.AccessOperation import AccessOperation
    from src.primitives.PathInfo import PathInfo
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)


class TestKVStoreSharedReadWriteStorage(unittest.TestCase):
    """KVStoreの共通読み書きストレージテストクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.credential_manager = CredentialManager(self.temp_dir)
        self.kvstore = KVStore(self.credential_manager)
        
        # テスト用の認証情報を登録
        mock_path_info = PathInfo(
            name="test_shared_user",
            path="/path/to/test_shared_user/module.py",
            type="test_services"
        )
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            self.credential_manager.register(AccessLevel.READ_WRITE)

    def tearDown(self):
        """各テストメソッド実行後のクリーンアップ処理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_shared_set_and_get(self):
        """共通読み書きストレージでのset/get操作テスト"""
        test_key = "shared_test_key"
        test_value = "shared_test_value"
        
        # 共通ストレージにデータを設定
        self.kvstore.shared_set(test_key, test_value)
        
        # データが取得できることを確認
        retrieved_value = self.kvstore.shared_get(test_key)
        self.assertEqual(retrieved_value, test_value)

    def test_shared_has_and_delete(self):
        """共通読み書きストレージでのhas/delete操作テスト"""
        test_key = "shared_delete_key"
        test_value = "shared_delete_value"
        
        # データを設定
        self.kvstore.shared_set(test_key, test_value)
        self.assertTrue(self.kvstore.shared_has(test_key))
        
        # データを削除
        self.kvstore.shared_delete(test_key)
        self.assertFalse(self.kvstore.shared_has(test_key))

    def test_shared_keys_and_values(self):
        """共通読み書きストレージでのkeys/values操作テスト"""
        test_data = {
            "shared_key1": "shared_value1",
            "shared_key2": "shared_value2",
            "shared_key3": "shared_value3"
        }
        
        # 複数のデータを設定
        for key, value in test_data.items():
            self.kvstore.shared_set(key, value)
        
        # キー一覧の確認
        keys = list(self.kvstore.shared_keys())
        for key in test_data.keys():
            self.assertIn(key, keys)
        
        # 値一覧の確認
        values = list(self.kvstore.shared_values())
        for value in test_data.values():
            self.assertIn(value, values)

    def test_shared_clear(self):
        """共通読み書きストレージでのclear操作テスト"""
        # データを設定
        self.kvstore.shared_set("clear_key1", "clear_value1")
        self.kvstore.shared_set("clear_key2", "clear_value2")
        
        # データが存在することを確認
        self.assertTrue(self.kvstore.shared_has("clear_key1"))
        self.assertTrue(self.kvstore.shared_has("clear_key2"))
        
        # クリア操作
        self.kvstore.shared_clear()
        
        # データが削除されていることを確認
        self.assertFalse(self.kvstore.shared_has("clear_key1"))
        self.assertFalse(self.kvstore.shared_has("clear_key2"))

    def test_shared_storage_isolation_from_private_storage(self):
        """共通ストレージとプライベートストレージの分離テスト"""
        test_key = "isolation_test_key"
        shared_value = "shared_value"
        private_value = "private_value"
        
        # テスト用のPathInfoを設定
        mock_path_info = PathInfo(
            name="isolation_test_user",
            path="/path/to/isolation_test_user/module.py",
            type="test_services"
        )
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            # 新しいユーザーの認証情報を登録
            self.credential_manager.register(AccessLevel.READ_WRITE)
            
            # 共通ストレージとプライベートストレージに同じキーで異なる値を設定
            self.kvstore.shared_set(test_key, shared_value)
            self.kvstore.set(test_key, private_value)
            
            # それぞれのストレージから正しい値が取得できることを確認
            self.assertEqual(self.kvstore.shared_get(test_key), shared_value)
            self.assertEqual(self.kvstore.get(test_key), private_value)

class TestKVStoreSharedReadOnlyStorage(unittest.TestCase):
    """KVStoreの共通読み込み専用ストレージテストクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.credential_manager = CredentialManager(self.temp_dir)
        self.kvstore = KVStore(self.credential_manager)
        
        # 管理者権限のテストユーザーを登録
        self.admin_path_info = PathInfo(
            name="test_admin_user",
            path="/path/to/test_admin_user/module.py",
            type="test_services"
        )
        
        # 一般ユーザー権限のテストユーザーを登録
        self.user_path_info = PathInfo(
            name="test_regular_user",
            path="/path/to/test_regular_user/module.py",
            type="test_services"
        )

    def tearDown(self):
        """各テストメソッド実行後のクリーンアップ処理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_admin_can_write_to_readonly_storage(self):
        """管理者が読み込み専用ストレージに書き込みできることのテスト"""
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.admin_path_info):
            # 管理者権限で登録
            self.credential_manager.register(AccessLevel.ADMIN)
            
            test_key = "admin_readonly_key"
            test_value = "admin_readonly_value"
            
            # 管理者は書き込み可能
            self.kvstore.readonly_set(test_key, test_value)
            
            # データが正しく設定されていることを確認
            retrieved_value = self.kvstore.readonly_get(test_key)
            self.assertEqual(retrieved_value, test_value)

    def test_regular_user_cannot_write_to_readonly_storage(self):
        """一般ユーザーが読み込み専用ストレージに書き込みできないことのテスト"""
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.user_path_info):
            # 一般ユーザー権限で登録
            self.credential_manager.register(AccessLevel.READ_WRITE)
            
            test_key = "user_readonly_key"
            test_value = "user_readonly_value"
            
            # 一般ユーザーは書き込み不可
            with self.assertRaises(PermissionError) as context:
                self.kvstore.readonly_set(test_key, test_value)
            
            self.assertIn("Admin access required", str(context.exception))

    def test_regular_user_can_read_from_readonly_storage(self):
        """一般ユーザーが読み込み専用ストレージから読み取りできることのテスト"""
        test_key = "readonly_read_key"
        test_value = "readonly_read_value"
        
        # 管理者がデータを設定
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.admin_path_info):
            self.credential_manager.register(AccessLevel.ADMIN)
            self.kvstore.readonly_set(test_key, test_value)
        
        # 一般ユーザーがデータを読み取り
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.user_path_info):
            self.credential_manager.register(AccessLevel.READ_WRITE)
            retrieved_value = self.kvstore.readonly_get(test_key)
            self.assertEqual(retrieved_value, test_value)

    def test_regular_user_cannot_delete_from_readonly_storage(self):
        """一般ユーザーが読み込み専用ストレージから削除できないことのテスト"""
        test_key = "readonly_delete_key"
        test_value = "readonly_delete_value"
        
        # 管理者がデータを設定
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.admin_path_info):
            self.credential_manager.register(AccessLevel.ADMIN)
            self.kvstore.readonly_set(test_key, test_value)
        
        # 一般ユーザーが削除を試行
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.user_path_info):
            self.credential_manager.register(AccessLevel.READ_WRITE)
            
            with self.assertRaises(PermissionError) as context:
                self.kvstore.readonly_delete(test_key)
            
            self.assertIn("Admin access required", str(context.exception))

    def test_admin_can_delete_from_readonly_storage(self):
        """管理者が読み込み専用ストレージから削除できることのテスト"""
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.admin_path_info):
            self.credential_manager.register(AccessLevel.ADMIN)
            
            test_key = "admin_delete_key"
            test_value = "admin_delete_value"
            
            # データを設定
            self.kvstore.readonly_set(test_key, test_value)
            self.assertTrue(self.kvstore.readonly_has(test_key))
            
            # データを削除
            self.kvstore.readonly_delete(test_key)
            self.assertFalse(self.kvstore.readonly_has(test_key))

    def test_regular_user_cannot_clear_readonly_storage(self):
        """一般ユーザーが読み込み専用ストレージをクリアできないことのテスト"""
        # 管理者がデータを設定
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.admin_path_info):
            self.credential_manager.register(AccessLevel.ADMIN)
            self.kvstore.readonly_set("clear_key1", "clear_value1")
            self.kvstore.readonly_set("clear_key2", "clear_value2")
        
        # 一般ユーザーがクリアを試行
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.user_path_info):
            self.credential_manager.register(AccessLevel.READ_WRITE)
            
            with self.assertRaises(PermissionError) as context:
                self.kvstore.readonly_clear()
            
            self.assertIn("Admin access required", str(context.exception))

    def test_admin_can_clear_readonly_storage(self):
        """管理者が読み込み専用ストレージをクリアできることのテスト"""
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=self.admin_path_info):
            self.credential_manager.register(AccessLevel.ADMIN)
            
            # データを設定
            self.kvstore.readonly_set("clear_key1", "clear_value1")
            self.kvstore.readonly_set("clear_key2", "clear_value2")
            
            # データが存在することを確認
            self.assertTrue(self.kvstore.readonly_has("clear_key1"))
            self.assertTrue(self.kvstore.readonly_has("clear_key2"))
            
            # クリア操作
            self.kvstore.readonly_clear()
            
            # データが削除されていることを確認
            self.assertFalse(self.kvstore.readonly_has("clear_key1"))
            self.assertFalse(self.kvstore.readonly_has("clear_key2"))


class TestKVStoreSharedStorageIntegration(unittest.TestCase):
    """KVStoreの共通ストレージ統合テストクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.credential_manager = CredentialManager(self.temp_dir)
        self.kvstore = KVStore(self.credential_manager)

    def tearDown(self):
        """各テストメソッド実行後のクリーンアップ処理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_three_storage_types_isolation(self):
        """3つのストレージタイプの分離性テスト"""
        # テスト用認証情報を登録
        mock_path_info = PathInfo(
            name="isolation_test_user",
            path="/path/to/isolation_test_user/module.py",
            type="test_services"
        )
        
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            self.credential_manager.register(AccessLevel.ADMIN)
            
            test_key = "isolation_key"
            private_value = "private_value"
            shared_rw_value = "shared_rw_value"
            shared_ro_value = "shared_ro_value"
            
            # 3つのストレージに同じキーで異なる値を設定
            self.kvstore.set(test_key, private_value)
            self.kvstore.shared_set(test_key, shared_rw_value)
            self.kvstore.readonly_set(test_key, shared_ro_value)
            
            # それぞれのストレージから正しい値が取得できることを確認
            self.assertEqual(self.kvstore.get(test_key), private_value)
            self.assertEqual(self.kvstore.shared_get(test_key), shared_rw_value)
            self.assertEqual(self.kvstore.readonly_get(test_key), shared_ro_value)

    def test_multiple_users_shared_storage_access(self):
        """複数ユーザーでの共通ストレージアクセステスト"""
        # ユーザー1のセットアップ
        user1_path_info = PathInfo(
            name="shared_user1",
            path="/path/to/shared_user1/module.py",
            type="test_services"
        )
        
        # ユーザー2のセットアップ
        user2_path_info = PathInfo(
            name="shared_user2",
            path="/path/to/shared_user2/module.py",
            type="test_services"
        )
        
        # ユーザー1が共通ストレージにデータを設定
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=user1_path_info):
            self.credential_manager.register(AccessLevel.READ_WRITE)
            self.kvstore.shared_set("multi_user_key", "user1_shared_value")
        
        # ユーザー2が同じデータを読み取り
        with patch.object(self.credential_manager.path_resolver, 'getPathInfo', return_value=user2_path_info):
            self.credential_manager.register(AccessLevel.READ_WRITE)
            retrieved_value = self.kvstore.shared_get("multi_user_key")
            self.assertEqual(retrieved_value, "user1_shared_value")


if __name__ == '__main__':
    # テストスイートの実行
    test_classes = [
        TestKVStoreSharedReadWriteStorage,
        TestKVStoreSharedReadOnlyStorage,
        TestKVStoreSharedStorageIntegration
    ]

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # テスト結果のサマリーを表示
    print(f"\n{'='*80}")
    print(f"KVStore共通ストレージテスト結果サマリー")
    print(f"{'='*80}")
    print(f"実行されたテスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.splitlines()[-1]}")
    
    if result.errors:
        print(f"\nエラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.splitlines()[-1]}")

#!/usr/bin/env python3
"""
CredentialManagerクラスの基本機能テストモジュール

【関連テストファイル】
- test_credential_security.py: アクセス制御・セキュリティテスト
- test_credential_integration.py: 統合テスト・エラーハンドリング
- test_immutable_credentials.py: Credentialsオブジェクトのimmutable性テスト

このテストモジュールはCredentialManagerクラスの以下の基本機能をテストします：
- 初期化処理の検証
- 認証情報の登録機能
- 基本的な認証情報検証機能
- 認証情報の存在確認・数量取得
- 重複登録の処理
"""

import sys
import os
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# テスト対象クラスのインポート
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try:
    from src.services.CredentialManager import CredentialManager
    from src.foundation.PathResolver import PathResolver
    from src.primitives.AccessLevel import AccessLevel
    from src.primitives.AccessOperation import AccessOperation
    from src.primitives.Credentials import Credentials
    from src.primitives.PathInfo import PathInfo
except ImportError as e:
    print(f"インポートエラーが発生しました: {e}")
    sys.exit(1)


class TestCredentialManager(unittest.TestCase):
    """CredentialManagerクラスの基本機能テストケース"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_base_path = os.path.join(self.temp_dir, "test_services")
        self.plugin_base_path = os.path.join(self.temp_dir, "plugin")
        
        # テスト用ディレクトリの作成
        os.makedirs(self.test_base_path, exist_ok=True)
        os.makedirs(self.plugin_base_path, exist_ok=True)
        
    def tearDown(self):
        """各テストメソッド実行後のクリーンアップ処理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_with_valid_path(self):
        """有効なパスでの初期化テスト"""
        manager = CredentialManager(self.test_base_path)
        
        # 初期状態の確認
        self.assertIsInstance(manager.path_resolver, PathResolver)
        self.assertEqual(manager.get_credential_count(), 0)
        
        # PathResolverが正しく初期化されているか確認（複数ベースパス対応）
        self.assertEqual(manager.path_resolver.base_paths[0], Path(self.test_base_path).resolve())

    def test_init_with_invalid_path(self):
        """無効なパスでの初期化時の例外テスト"""
        with self.assertRaises(ValueError):
            CredentialManager("")
        
        with self.assertRaises(ValueError):
            CredentialManager(None)

    def test_get_credential_count_empty(self):
        """空の状態での認証情報数取得テスト"""
        manager = CredentialManager(self.test_base_path)
        
        self.assertEqual(manager.get_credential_count(), 0)

    def test_has_credential_empty(self):
        """空の状態での認証情報存在チェックテスト"""
        manager = CredentialManager(self.test_base_path)
        
        self.assertFalse(manager.has_credential("test_caller"))
        self.assertFalse(manager.has_credential("nonexistent"))

    def test_register_read_only_credential(self):
        """READ_ONLY権限での認証情報登録テスト"""
        manager = CredentialManager(self.test_base_path)
        
        # PathResolverのgetPathInfoをモック
        mock_path_info = PathInfo(
            name="test_caller",
            path="/path/to/test_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            credential = manager.register(AccessLevel.READ_ONLY)
            
            # 返却された認証情報の検証
            self.assertIsInstance(credential, Credentials)
            self.assertEqual(credential.name, "test_caller")
            self.assertEqual(credential.access_level, AccessLevel.READ_ONLY)
            self.assertEqual(credential.path, "/path/to/test_caller/module.py")
            self.assertEqual(credential.type, "test_services")
            self.assertFalse(credential.enabled)  # 初期状態では無効
            self.assertTrue(credential.key.startswith("test_caller_"))
            
            # 内部状態の確認
            self.assertEqual(manager.get_credential_count(), 1)
            self.assertTrue(manager.has_credential("test_caller"))

    def test_register_read_write_credential(self):
        """READ_WRITE権限での認証情報登録テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="rw_caller",
            path="/path/to/rw_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            credential = manager.register(AccessLevel.READ_WRITE)
            
            self.assertEqual(credential.access_level, AccessLevel.READ_WRITE)
            self.assertEqual(credential.name, "rw_caller")

    def test_register_write_only_credential(self):
        """WRITE_ONLY権限での認証情報登録テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="wo_caller",
            path="/path/to/wo_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            credential = manager.register(AccessLevel.WRITE_ONLY)
            
            self.assertEqual(credential.access_level, AccessLevel.WRITE_ONLY)
            self.assertEqual(credential.name, "wo_caller")

    def test_register_multiple_credentials(self):
        """複数の認証情報登録テスト"""
        manager = CredentialManager(self.test_base_path)
        
        callers = [
            ("caller1", AccessLevel.READ_ONLY),
            ("caller2", AccessLevel.READ_WRITE),
            ("caller3", AccessLevel.WRITE_ONLY)
        ]
        
        for caller_name, access_level in callers:
            mock_path_info = PathInfo(
                name=caller_name,
                path=f"/path/to/{caller_name}/module.py",
                type="test_services"
            )
            
            with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
                manager.register(access_level)
        
        # すべて登録されていることを確認
        self.assertEqual(manager.get_credential_count(), 3)
        for caller_name, _ in callers:
            self.assertTrue(manager.has_credential(caller_name))

    def test_register_duplicate_caller_overwrites(self):
        """同一呼び出し元の重複登録時の上書きテスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="duplicate_caller",
            path="/path/to/duplicate_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            # 最初の登録
            credential1 = manager.register(AccessLevel.READ_ONLY)
            
            # 同じ呼び出し元で再登録
            credential2 = manager.register(AccessLevel.READ_WRITE)
            
            # 上書きされていることを確認
            self.assertEqual(manager.get_credential_count(), 1)
            self.assertEqual(credential1.name, credential2.name)
            self.assertNotEqual(credential1.access_level, credential2.access_level)
            self.assertNotEqual(credential1.key, credential2.key)

    def test_validate_with_valid_read_operation(self):
        """有効な読み取り操作の検証テスト"""
        manager = CredentialManager(self.test_base_path)
        
        # 認証情報を登録
        mock_path_info = PathInfo(
            name="read_caller",
            path="/path/to/read_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            manager.register(AccessLevel.READ_ONLY)
            
            # 読み取り操作の検証
            result = manager.validate(AccessOperation.READ)
            self.assertTrue(result)

    def test_validate_with_invalid_write_operation_for_read_only(self):
        """READ_ONLY権限での無効な書き込み操作の検証テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="read_only_caller",
            path="/path/to/read_only_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            manager.register(AccessLevel.READ_ONLY)
            
            # 書き込み操作は拒否されるはず
            result = manager.validate(AccessOperation.WRITE)
            self.assertFalse(result)

    def test_validate_with_read_write_operations(self):
        """READ_WRITE権限での両操作の検証テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="rw_caller",
            path="/path/to/rw_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            manager.register(AccessLevel.READ_WRITE)
            
            # 両方の操作が許可されるはず
            self.assertTrue(manager.validate(AccessOperation.READ))
            self.assertTrue(manager.validate(AccessOperation.WRITE))

    def test_validate_with_unregistered_caller(self):
        """未登録の呼び出し元による検証テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="unregistered_caller",
            path="/path/to/unregistered_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            # 認証情報未登録状態で検証
            result = manager.validate(AccessOperation.READ)
            self.assertFalse(result)

    def test_getCredential_with_valid_read_operation(self):
        """有効な読み取り操作での認証情報取得テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="getter_caller",
            path="/path/to/getter_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            # 認証情報を登録
            original_credential = manager.register(AccessLevel.READ_ONLY)
            
            # 認証情報を取得
            retrieved_credential = manager.getCredential(AccessOperation.READ)
            
            # 取得した認証情報の検証
            self.assertIsInstance(retrieved_credential, Credentials)
            self.assertEqual(retrieved_credential.name, "getter_caller")
            self.assertEqual(retrieved_credential.access_level, AccessLevel.READ_ONLY)
            self.assertTrue(retrieved_credential.enabled)  # 有効化されている
            self.assertGreater(retrieved_credential.access_count, original_credential.access_count)

    def test_getCredential_with_invalid_operation(self):
        """無効な操作での認証情報取得時の例外テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="invalid_caller",
            path="/path/to/invalid_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            # READ_ONLY権限で登録
            manager.register(AccessLevel.READ_ONLY)
            
            # WRITE操作は許可されないため例外が発生するはず
            with self.assertRaises(ValueError) as context:
                manager.getCredential(AccessOperation.WRITE)
            
            self.assertEqual(
                str(context.exception),
                "Invalid credential: invalid_caller for operation: AccessOperation.WRITE"
            )

    def test_getCredential_with_unregistered_caller(self):
        """未登録の呼び出し元での認証情報取得時の例外テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="unregistered_caller",
            path="/path/to/unregistered_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            # 認証情報未登録で取得を試行
            with self.assertRaises(ValueError) as context:
                manager.getCredential(AccessOperation.READ)
            
            self.assertEqual(
                str(context.exception),
                "Invalid credential: unregistered_caller for operation: AccessOperation.READ"
            )

    def test_getKey_with_registered_credential(self):
        """登録済み認証情報でのキー取得テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="key_getter",
            path="/path/to/key_getter/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            # 認証情報を登録
            credential = manager.register(AccessLevel.READ_ONLY)
            
            # キーを取得
            retrieved_key = manager.getKey()
            
            # キー検証
            self.assertIsInstance(retrieved_key, str)
            self.assertEqual(retrieved_key, credential.key)
            self.assertTrue(retrieved_key.startswith("key_getter_"))
            self.assertGreater(len(retrieved_key), len("key_getter_"))

    def test_getKey_with_unregistered_caller(self):
        """未登録の呼び出し元でのキー取得時の例外テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="unregistered_key_caller",
            path="/path/to/unregistered_key_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            # 未登録状態でキー取得を試行
            with self.assertRaises(ValueError) as context:
                manager.getKey()
            
            self.assertEqual(
                str(context.exception),
                "No valid credential found for caller: unregistered_key_caller"
            )

    def test_getKey_after_credential_overwrite(self):
        """認証情報上書き後のキー取得テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="overwrite_caller",
            path="/path/to/overwrite_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            # 最初の認証情報を登録
            first_credential = manager.register(AccessLevel.READ_ONLY)
            first_key = manager.getKey()
            self.assertEqual(first_key, first_credential.key)
            
            # 同一呼び出し元で異なるアクセスレベルで再登録（上書き）
            second_credential = manager.register(AccessLevel.READ_WRITE)
            second_key = manager.getKey()
            
            # 新しい認証情報のキーが取得されることを確認
            self.assertEqual(second_key, second_credential.key)
            self.assertNotEqual(second_key, first_key)


if __name__ == "__main__":
    # テストスイートの実行
    unittest.main(verbosity=2)

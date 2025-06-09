#!/usr/bin/env python3
"""
CredentialManagerのimmutable性をテストするテストモジュール

【関連テストファイル】
- test_credential_manager.py: 基本機能テスト
- test_credential_security.py: アクセス制御・セキュリティテスト  
- test_credential_integration.py: 統合テスト・エラーハンドリング

このテストモジュールはCredentialManagerクラスの以下のimmutable特性をテストします：
- Credentialsオブジェクトのfrozen特性の検証
- immutableパターンによる新しいインスタンス生成の検証
- 外部からの改変に対する保護機能の検証
"""

import sys
import os
import unittest
import tempfile
import shutil
from unittest.mock import patch

# テスト対象クラスのインポート
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try:
    from src.foundation.ProtectedStore import ProtectedStore
    from src.services.CredentialManager import CredentialManager
    from src.primitives.AccessLevel import AccessLevel
    from src.primitives.AccessOperation import AccessOperation
    from src.primitives.Credentials import Credentials
    from src.primitives.PathInfo import PathInfo
except ImportError as e:
    print(f"インポートエラーが発生しました: {e}")
    sys.exit(1)


class TestCredentialManagerImmutability(unittest.TestCase):
    """CredentialManagerのimmutable性をテストするクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_base_path = os.path.join(self.temp_dir, "test_services")
        os.makedirs(self.test_base_path, exist_ok=True)
        
    def tearDown(self):
        """各テストメソッド実行後のクリーンアップ処理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_credentials_object_is_frozen(self):
        """Credentialsオブジェクトがfrozen dataclassであることのテスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="test_caller",
            path="/path/to/test_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            credential = manager.register(AccessLevel.READ_WRITE)
        
        # frozen dataclassのため、属性の変更は例外を発生させる
        with self.assertRaises(Exception) as context:
            credential.enabled = True
        
        # FrozenInstanceErrorまたはAttributeErrorが発生することを確認
        self.assertIn("frozen", str(type(context.exception)).lower())

    def test_immutable_pattern_creates_new_instance(self):
        """immutableパターンで新しいインスタンスが生成されることのテスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="test_caller",
            path="/path/to/test_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            original_credential = manager.register(AccessLevel.READ_WRITE)
        
        # immutableパターンで新しいインスタンスを生成
        updated_credential = original_credential.with_updated_access()
        
        # 異なるインスタンスであることを確認
        self.assertIsNot(original_credential, updated_credential)
        
        # 元のインスタンスは変更されていないことを確認
        self.assertFalse(original_credential.enabled)
        self.assertEqual(original_credential.access_count, 0)
        
        # 新しいインスタンスは更新されていることを確認
        self.assertTrue(updated_credential.enabled)
        self.assertEqual(updated_credential.access_count, 1)
        
        # 不変の属性は同じであることを確認
        self.assertEqual(original_credential.name, updated_credential.name)
        self.assertEqual(original_credential.key, updated_credential.key)
        self.assertEqual(original_credential.access_level, updated_credential.access_level)

    def test_enable_credentials_preserves_immutability(self):
        """_enableCredentials内でのimmutableパターンの適用テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="test_caller",
            path="/path/to/test_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            original_credential = manager.register(AccessLevel.READ_WRITE)
            
            # getCredentialを通じて_enableCredentialsを実行
            enabled_credential = manager.getCredential(AccessOperation.READ)
        
        # 返されたインスタンスが有効化されていることを確認
        self.assertTrue(enabled_credential.enabled)
        self.assertEqual(enabled_credential.access_count, 1)


class TestCredentialManagerImmutabilityEdgeCases(unittest.TestCase):
    """CredentialManagerのimmutable性に関する境界条件テストクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_base_path = os.path.join(self.temp_dir, "test_services")
        os.makedirs(self.test_base_path, exist_ok=True)
        
    def tearDown(self):
        """各テストメソッド実行後のクリーンアップ処理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_credentials_with_different_access_levels_immutability(self):
        """異なるアクセスレベルでのimmutable性テスト"""
        manager = CredentialManager(self.test_base_path)
        
        access_levels = [
            AccessLevel.READ_ONLY,
            AccessLevel.WRITE_ONLY,
            AccessLevel.READ_WRITE
        ]
        
        # 異なるアクセスレベルで認証情報を登録
        for i, access_level in enumerate(access_levels):
            mock_path_info = PathInfo(
                name=f"caller_{i}",
                path=f"/path/to/caller_{i}/module.py",
                type="test_services"
            )
            
            with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
                credential = manager.register(access_level)
                
                # 各認証情報がfrozenであることを確認
                with self.assertRaises(Exception):
                    credential.access_level = AccessLevel.ADMIN

    def test_with_updated_access_parameter_validation(self):
        """with_updated_accessメソッドのパラメータ検証テスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="test_caller",
            path="/path/to/test_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            original_credential = manager.register(AccessLevel.READ_WRITE)
        
        # カスタムパラメータでの更新テスト
        custom_time = 1234567890.0
        custom_count = 42
        
        updated_credential = original_credential.with_updated_access(
            last_access=custom_time,
            access_count=custom_count
        )
        
        # カスタムパラメータが正しく設定されていることを確認
        self.assertEqual(updated_credential.last_access, custom_time)
        self.assertEqual(updated_credential.access_count, custom_count)
        self.assertTrue(updated_credential.enabled)
        
        # 元のインスタンスは変更されていないことを確認
        self.assertNotEqual(original_credential.last_access, custom_time)
        self.assertNotEqual(original_credential.access_count, custom_count)
        self.assertFalse(original_credential.enabled)


class TestCredentialManagerImmutabilityErrorHandling(unittest.TestCase):
    """CredentialManagerのimmutable性に関するエラーハンドリングテストクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_base_path = os.path.join(self.temp_dir, "test_services")
        os.makedirs(self.test_base_path, exist_ok=True)
        
    def tearDown(self):
        """各テストメソッド実行後のクリーンアップ処理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_frozen_attribute_modification_error_handling(self):
        """frozen属性変更時のエラーハンドリングテスト"""
        manager = CredentialManager(self.test_base_path)
        
        mock_path_info = PathInfo(
            name="error_test_caller",
            path="/path/to/error_test_caller/module.py",
            type="test_services"
        )
        
        with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
            credential = manager.register(AccessLevel.READ_WRITE)
        
        # 各frozen属性の変更試行でエラーが発生することを確認
        frozen_attributes = [
            ('name', 'new_name'),
            ('key', 'new_key'),
            ('access_level', AccessLevel.ADMIN),
            ('enabled', True),
            ('created_at', 9999999.0),
            ('last_access', 9999999.0),
            ('access_count', 999)
        ]
        
        for attr_name, new_value in frozen_attributes:
            with self.subTest(attribute=attr_name):
                with self.assertRaises(Exception):
                    setattr(credential, attr_name, new_value)

if __name__ == "__main__":
    # テストスイートの実行
    # 各テストクラスを個別に実行して詳細な結果を表示
    test_classes = [
        TestCredentialManagerImmutability,
        TestCredentialManagerImmutabilityEdgeCases,
        TestCredentialManagerImmutabilityErrorHandling
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
    print(f"Immutable性テスト結果サマリー")
    print(f"{'='*80}")
    print(f"実行されたテスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")
    print(f"{'='*80}")
    
    # 終了コードを設定
    sys.exit(0 if result.wasSuccessful() else 1)

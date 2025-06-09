#!/usr/bin/env python3
"""
CredentialManagerクラスのアクセス制御・セキュリティテストモジュール

【関連テストファイル】
- test_credential_manager.py: 基本機能テスト（初期化、登録、基本検証）
- test_credential_integration.py: 統合テスト・エラーハンドリング
- test_immutable_credentials.py: Credentialsオブジェクトのimmutable性テスト

このテストモジュールはCredentialManagerクラスの以下のセキュリティ機能をテストします：
- 管理者権限への昇格可能性の判定
- アクセス制御の検証
- アクセスレベル階層の検証
- キー生成とアクセス制御
- セキュリティ境界の検証
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


class TestCredentialManagerSecurity(unittest.TestCase):
	"""CredentialManagerのセキュリティ機能テストケース"""

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

	def test_canEscalateToAdmin_with_plugin_type(self):
		"""pluginタイプでの管理者昇格不可テスト"""
		manager = CredentialManager(self.plugin_base_path)
		
		mock_path_info = PathInfo(
			name="test_plugin",
			path="/path/to/test_plugin/plugin.py",
			type="plugin"
		)
		
		result = manager.canEscalateToAdmin(mock_path_info)
		self.assertFalse(result)

	def test_canEscalateToAdmin_with_unknown_type(self):
		"""unknownタイプでの管理者昇格不可テスト"""
		manager = CredentialManager(self.test_base_path)
		
		mock_path_info = PathInfo(
			name="unknown_caller",
			path="/path/to/unknown_caller/module.py",
			type="unknown"
		)
		
		result = manager.canEscalateToAdmin(mock_path_info)
		self.assertFalse(result)

	def test_canEscalateToAdmin_with_services_type(self):
		"""servicesタイプでの管理者昇格可能テスト"""
		manager = CredentialManager(self.test_base_path)
		
		mock_path_info = PathInfo(
			name="service_caller",
			path="/path/to/service_caller/service.py",
			type="services"
		)
		
		result = manager.canEscalateToAdmin(mock_path_info)
		self.assertTrue(result)

	def test_canEscalateToAdmin_with_foundation_type(self):
		"""foundationタイプでの管理者昇格可能テスト"""
		foundation_base_path = os.path.join(self.temp_dir, "foundation")
		os.makedirs(foundation_base_path, exist_ok=True)
		manager = CredentialManager(foundation_base_path)
		
		mock_path_info = PathInfo(
			name="foundation_caller",
			path="/path/to/foundation_caller/foundation.py",
			type="foundation"
		)
		
		result = manager.canEscalateToAdmin(mock_path_info)
		self.assertTrue(result)

	def test_canEscalateToAdmin_with_mixed_plugin_type(self):
		"""部分的にpluginを含むタイプでの昇格不可テスト"""
		mixed_plugin_base_path = os.path.join(self.temp_dir, "user_plugin")
		os.makedirs(mixed_plugin_base_path, exist_ok=True)
		manager = CredentialManager(mixed_plugin_base_path)
		
		mock_path_info = PathInfo(
			name="user_plugin_caller",
			path="/path/to/user_plugin_caller/plugin.py",
			type="user_plugin"
		)
		
		result = manager.canEscalateToAdmin(mock_path_info)
		self.assertFalse(result)

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

	def test_validate_with_write_only_operations(self):
		"""WRITE_ONLY権限での操作検証テスト"""
		manager = CredentialManager(self.test_base_path)
		
		mock_path_info = PathInfo(
			name="wo_caller",
			path="/path/to/wo_caller/module.py",
			type="test_services"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
			manager.register(AccessLevel.WRITE_ONLY)
			
			# 書き込みのみ許可、読み取りは拒否
			self.assertTrue(manager.validate(AccessOperation.WRITE))
			self.assertFalse(manager.validate(AccessOperation.READ))

	def test_validate_with_admin_operations(self):
		"""ADMIN権限での全操作検証テスト"""
		manager = CredentialManager(self.test_base_path)
		
		mock_path_info = PathInfo(
			name="admin_caller",
			path="/path/to/admin_caller/module.py",
			type="test_services"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
			manager.register(AccessLevel.ADMIN)
			
			# 全操作が許可されるはず
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

	def test_access_level_hierarchy_validation(self):
		"""アクセスレベル階層の検証テスト"""
		manager = CredentialManager(self.test_base_path)
		
		# 各アクセスレベルでの権限テスト
		test_cases = [
			(AccessLevel.ADMIN, [AccessOperation.READ, AccessOperation.WRITE]),
			(AccessLevel.READ_WRITE, [AccessOperation.READ, AccessOperation.WRITE]),
			(AccessLevel.READ_ONLY, [AccessOperation.READ]),
			(AccessLevel.WRITE_ONLY, [AccessOperation.WRITE])
		]
		
		for access_level, allowed_operations in test_cases:
			with self.subTest(access_level=access_level):
				# サブテスト用のマネージャーを作成
				sub_manager = CredentialManager(self.test_base_path)
				
				mock_path_info = PathInfo(
					name=f"{access_level.value}_caller",
					path=f"/path/to/{access_level.value}_caller/module.py",
					type="test_services"
				)
				
				with patch.object(sub_manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
					# ADMIN権限の場合も普通に登録（type="test_services"なので昇格可能）
					sub_manager.register(access_level)
					
					# 許可された操作をテスト
					for operation in allowed_operations:
						self.assertTrue(sub_manager.validate(operation))
					
					# 許可されていない操作をテスト
					all_operations = [AccessOperation.READ, AccessOperation.WRITE]
					denied_operations = [op for op in all_operations if op not in allowed_operations]
					
					for operation in denied_operations:
						self.assertFalse(sub_manager.validate(operation))

	def test_admin_escalation_with_escalation_allowed(self):
		"""昇格可能な環境でのADMIN権限登録テスト"""
		manager = CredentialManager(self.test_base_path)
		
		mock_path_info = PathInfo(
			name="admin_caller",
			path="/path/to/admin_caller/module.py",
			type="test_services"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
			credential = manager.register(AccessLevel.ADMIN)
			
			self.assertEqual(credential.access_level, AccessLevel.ADMIN)
			self.assertEqual(credential.name, "admin_caller")

	def test_admin_escalation_with_escalation_denied(self):
		"""昇格不可能な環境でのADMIN権限登録時の例外テスト"""
		manager = CredentialManager(self.plugin_base_path)
		
		mock_path_info = PathInfo(
			name="plugin_caller",
			path="/path/to/plugin_caller/module.py",
			type="plugin"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
			with self.assertRaises(ValueError) as context:
				manager.register(AccessLevel.ADMIN)
			
			self.assertEqual(
				str(context.exception),
				"Admin access level is not allowed for caller: plugin_caller"
			)


class TestCredentialManagerKeyAccess(unittest.TestCase):
	"""CredentialManagerのキーアクセス制御テストケース"""

	def setUp(self):
		"""各テストメソッド実行前の初期化処理"""
		self.temp_dir = tempfile.mkdtemp()
		self.test_base_path = os.path.join(self.temp_dir, "test_services")
		os.makedirs(self.test_base_path, exist_ok=True)

	def tearDown(self):
		"""各テストメソッド実行後のクリーンアップ処理"""
		if os.path.exists(self.temp_dir):
			shutil.rmtree(self.temp_dir)

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

	def test_getKey_with_multiple_registered_credentials(self):
		"""複数の認証情報が登録されている状況での正しいキー取得テスト"""
		manager = CredentialManager(self.test_base_path)
		
		# 最初の認証情報を登録
		first_mock_path_info = PathInfo(
			name="first_caller",
			path="/path/to/first_caller/module.py",
			type="test_services"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=first_mock_path_info):
			first_credential = manager.register(AccessLevel.READ_ONLY)
		
		# 2番目の認証情報を登録
		second_mock_path_info = PathInfo(
			name="second_caller",
			path="/path/to/second_caller/module.py",
			type="test_services"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=second_mock_path_info):
			second_credential = manager.register(AccessLevel.READ_WRITE)
		
		# 最初の呼び出し元としてキーを取得
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=first_mock_path_info):
			first_key = manager.getKey()
			self.assertEqual(first_key, first_credential.key)
			self.assertNotEqual(first_key, second_credential.key)
		
		# 2番目の呼び出し元としてキーを取得
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=second_mock_path_info):
			second_key = manager.getKey()
			self.assertEqual(second_key, second_credential.key)
			self.assertNotEqual(second_key, first_credential.key)

	def test_getKey_with_different_access_levels(self):
		"""異なるアクセスレベルでの認証情報に対するキー取得テスト"""
		manager = CredentialManager(self.test_base_path)
		
		access_levels = [
			AccessLevel.READ_ONLY,
			AccessLevel.WRITE_ONLY,
			AccessLevel.READ_WRITE,
			AccessLevel.ADMIN
		]
		
		registered_credentials = {}
		
		# 各アクセスレベルで認証情報を登録
		for i, access_level in enumerate(access_levels):
			caller_name = f"caller_{access_level.name.lower()}"
			mock_path_info = PathInfo(
				name=caller_name,
				path=f"/path/to/{caller_name}/module.py",
				type="test_services"
			)
			
			with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
				credential = manager.register(access_level)
				registered_credentials[caller_name] = credential
		
		# 各呼び出し元として正しいキーが取得できることを確認
		for caller_name, expected_credential in registered_credentials.items():
			mock_path_info = PathInfo(
				name=caller_name,
				path=f"/path/to/{caller_name}/module.py",
				type="test_services"
			)
			
			with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
				retrieved_key = manager.getKey()
				self.assertEqual(retrieved_key, expected_credential.key)
				self.assertTrue(retrieved_key.startswith(f"{caller_name}_"))

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

	def test_key_generation_uniqueness(self):
		"""キー生成の一意性テスト"""
		manager = CredentialManager(self.test_base_path)
		
		generated_keys = set()
		
		for i in range(100):  # 100回生成して重複がないかテスト
			mock_path_info = PathInfo(
				name=f"unique_caller_{i}",
				path=f"/path/to/unique_caller_{i}/module.py",
				type="test_services"
			)
			
			with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
				credential = manager.register(AccessLevel.READ_ONLY)
				generated_keys.add(credential.key)
		
		# すべてのキーが一意であることを確認
		self.assertEqual(len(generated_keys), 100)


class TestCredentialManagerAccessControl(unittest.TestCase):
	"""CredentialManagerの認証情報取得・アクセス制御テストケース"""

	def setUp(self):
		"""各テストメソッド実行前の初期化処理"""
		self.temp_dir = tempfile.mkdtemp()
		self.test_base_path = os.path.join(self.temp_dir, "test_services")
		os.makedirs(self.test_base_path, exist_ok=True)

	def tearDown(self):
		"""各テストメソッド実行後のクリーンアップ処理"""
		if os.path.exists(self.temp_dir):
			shutil.rmtree(self.temp_dir)

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

	def test_enableCredentials_immutable_pattern(self):
		"""_enableCredentialsメソッドのimmutableパターンテスト"""
		manager = CredentialManager(self.test_base_path)
		
		mock_path_info = PathInfo(
			name="immutable_caller",
			path="/path/to/immutable_caller/module.py",
			type="test_services"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
			# 認証情報を登録
			original_credential = manager.register(AccessLevel.READ_ONLY)
			
			# 元の認証情報の状態を記録
			original_enabled = original_credential.enabled
			original_access_count = original_credential.access_count
			
			# 認証情報を有効化（内部メソッドを直接テスト）
			enabled_credential = manager._enableCredentials(original_credential)
			
			# 元の認証情報は変更されていないことを確認
			self.assertEqual(original_credential.enabled, original_enabled)
			self.assertEqual(original_credential.access_count, original_access_count)
			
			# 新しい認証情報は更新されていることを確認
			self.assertTrue(enabled_credential.enabled)
			self.assertGreater(enabled_credential.access_count, original_access_count)


if __name__ == "__main__":
	# テストスイートの実行
	unittest.main(verbosity=2)

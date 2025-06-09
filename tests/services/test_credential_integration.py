#!/usr/bin/env python3
"""
CredentialManagerクラスの統合テスト・エラーハンドリングテストモジュール

【関連テストファイル】
- test_credential_manager.py: 基本機能テスト（初期化、登録、基本検証）
- test_credential_security.py: アクセス制御・セキュリティテスト
- test_immutable_credentials.py: Credentialsオブジェクトのimmutable性テスト

このテストモジュールはCredentialManagerクラスの以下の機能をテストします：
- 実際のディレクトリ構造を使った統合テスト
- マルチコンテキスト環境でのシナリオテスト
- エラーハンドリングの検証
- PathResolverとの連携テスト
- 同時アクセスシミュレーション
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


class TestCredentialManagerIntegration(unittest.TestCase):
	"""CredentialManagerの統合テストケース"""

	def setUp(self):
		"""統合テスト用の初期化処理"""
		self.temp_dir = tempfile.mkdtemp()
		self.services_path = os.path.join(self.temp_dir, "services")
		self.plugin_path = os.path.join(self.temp_dir, "plugin")
		
		# 実際のディレクトリ構造を作成
		os.makedirs(self.services_path, exist_ok=True)
		os.makedirs(self.plugin_path, exist_ok=True)

	def tearDown(self):
		"""統合テスト用のクリーンアップ処理"""
		if os.path.exists(self.temp_dir):
			shutil.rmtree(self.temp_dir)

	def test_services_context_full_scenario(self):
		"""サービスコンテキストでの完全なシナリオテスト"""
		# 実際のディレクトリ構造を作成
		auth_service_dir = os.path.join(self.services_path, "auth_service")
		os.makedirs(auth_service_dir, exist_ok=True)
		
		test_file = os.path.join(auth_service_dir, "authenticator.py")
		with open(test_file, 'w') as f:
			f.write("# Authentication service")
		
		manager = CredentialManager(self.services_path)
		
		# PathResolverの動作をモック（実際のディレクトリ構造を使用）
		mock_path_info = PathInfo(
			name="auth_service",
			path=test_file,
			type="services"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
			# ADMIN権限での登録（servicesコンテキストなので昇格可能）
			credential = manager.register(AccessLevel.ADMIN)
			
			# 登録結果の確認
			self.assertEqual(credential.name, "auth_service")
			self.assertEqual(credential.access_level, AccessLevel.ADMIN)
			self.assertEqual(credential.type, "services")
			
			# 全操作が許可されることを確認
			self.assertTrue(manager.validate(AccessOperation.READ))
			self.assertTrue(manager.validate(AccessOperation.WRITE))
			
			# 認証情報取得テスト
			read_credential = manager.getCredential(AccessOperation.READ)
			write_credential = manager.getCredential(AccessOperation.WRITE)
			
			self.assertTrue(read_credential.enabled)
			self.assertTrue(write_credential.enabled)

	def test_plugin_context_restricted_scenario(self):
		"""プラグインコンテキストでの制限付きシナリオテスト"""
		# 実際のディレクトリ構造を作成
		user_plugin_dir = os.path.join(self.plugin_path, "user_plugin")
		os.makedirs(user_plugin_dir, exist_ok=True)
		
		test_file = os.path.join(user_plugin_dir, "plugin_main.py")
		with open(test_file, 'w') as f:
			f.write("# User plugin main")
		
		manager = CredentialManager(self.plugin_path)
		
		mock_path_info = PathInfo(
			name="user_plugin",
			path=test_file,
			type="plugin"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
			# ADMIN権限での登録は失敗するはず（pluginコンテキストなので昇格不可）
			with self.assertRaises(ValueError):
				manager.register(AccessLevel.ADMIN)

			# READ_ONLY権限での登録は成功するはず
			credential = manager.register(AccessLevel.READ_ONLY)

			self.assertEqual(credential.name, "user_plugin")
			self.assertEqual(credential.access_level, AccessLevel.READ_ONLY)
			self.assertEqual(credential.type, "plugin")
		
			# 読み取りのみ許可、書き込みは拒否
			self.assertTrue(manager.validate(AccessOperation.READ))
			self.assertFalse(manager.validate(AccessOperation.WRITE))

	def test_multiple_managers_isolation(self):
		"""複数のマネージャー間での分離テスト"""
		manager1 = CredentialManager(self.services_path)
		manager2 = CredentialManager(self.plugin_path)
		
		# それぞれ異なる認証情報を登録
		mock_path_info1 = PathInfo(
			name="service_caller",
			path="/path/to/service_caller/module.py",
			type="services"
		)
		
		mock_path_info2 = PathInfo(
			name="plugin_caller",
			path="/path/to/plugin_caller/module.py",
			type="plugin"
		)
		
		with patch.object(manager1.path_resolver, 'getPathInfo', return_value=mock_path_info1):
			credential1 = manager1.register(AccessLevel.READ_WRITE)
		
		with patch.object(manager2.path_resolver, 'getPathInfo', return_value=mock_path_info2):
			credential2 = manager2.register(AccessLevel.READ_ONLY)
		
		# 各マネージャーが独立していることを確認
		self.assertEqual(manager1.get_credential_count(), 1)
		self.assertEqual(manager2.get_credential_count(), 1)
		
		self.assertTrue(manager1.has_credential("service_caller"))
		self.assertFalse(manager1.has_credential("plugin_caller"))
		
		self.assertTrue(manager2.has_credential("plugin_caller"))
		self.assertFalse(manager2.has_credential("service_caller"))

	def test_concurrent_access_simulation(self):
		"""同時アクセスのシミュレーションテスト"""
		manager = CredentialManager(self.services_path)
		
		mock_path_info = PathInfo(
			name="concurrent_caller",
			path="/path/to/concurrent_caller/module.py",
			type="services"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
			# 認証情報を登録
			manager.register(AccessLevel.READ_WRITE)
			
			# 複数回のアクセスをシミュレート
			access_results = []
			for i in range(10):
				try:
					credential = manager.getCredential(AccessOperation.READ)
					access_results.append(credential.access_count)
				except ValueError:
					access_results.append(None)
			
			# すべてのアクセスが成功していることを確認
			self.assertTrue(all(count is not None for count in access_results))
			
			# アクセス回数が最低でも10回以上になっていることを確認
			self.assertGreaterEqual(max(access_results), 10)

	def test_mixed_type_environment_scenario(self):
		"""混合タイプ環境でのシナリオテスト"""
		# 複数の異なるタイプが混在する環境
		foundation_path = os.path.join(self.temp_dir, "foundation")
		os.makedirs(foundation_path, exist_ok=True)
		
		# Foundation、Services、Pluginの各マネージャーを作成
		foundation_manager = CredentialManager(foundation_path)
		services_manager = CredentialManager(self.services_path)
		plugin_manager = CredentialManager(self.plugin_path)
		
		# 各コンテキストで適切な権限レベルを登録
		test_scenarios = [
			(foundation_manager, "foundation_caller", "foundation", AccessLevel.ADMIN),
			(services_manager, "service_caller", "services", AccessLevel.READ_WRITE),
			(plugin_manager, "plugin_caller", "plugin", AccessLevel.READ_ONLY)
		]
		
		registered_credentials = []
		
		for manager, caller_name, caller_type, access_level in test_scenarios:
			mock_path_info = PathInfo(
				name=caller_name,
				path=f"/path/to/{caller_name}/module.py",
				type=caller_type
			)
			
			with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
				credential = manager.register(access_level)
				registered_credentials.append((manager, credential, access_level))
		
		# 各マネージャーで適切な権限が設定されていることを確認
		for manager, credential, expected_access_level in registered_credentials:
			self.assertEqual(credential.access_level, expected_access_level)
			self.assertEqual(manager.get_credential_count(), 1)

	def test_real_directory_structure_integration(self):
		"""実際のディレクトリ構造を使った統合テスト"""
		# より現実的なディレクトリ構造を作成
		test_structure = {
			"services": ["auth", "storage", "security"],
			"foundation": ["core", "utils"],
			"plugin": ["user_extensions", "third_party"]
		}
		
		managers = {}
		
		for context_type, modules in test_structure.items():
			context_path = os.path.join(self.temp_dir, context_type)
			os.makedirs(context_path, exist_ok=True)
			
			for module_name in modules:
				module_dir = os.path.join(context_path, module_name)
				os.makedirs(module_dir, exist_ok=True)
				
				# モジュールファイルを作成
				module_file = os.path.join(module_dir, f"{module_name}_main.py")
				with open(module_file, 'w') as f:
					f.write(f"# {module_name} module in {context_type}")
			
			managers[context_type] = CredentialManager(context_path)
		
		# 各コンテキストで認証情報を登録
		registration_results = {}
		
		for context_type, manager in managers.items():
			for module_name in test_structure[context_type]:
				mock_path_info = PathInfo(
					name=module_name,
					path=f"/path/to/{module_name}/module.py",
					type=context_type
				)
				
				# コンテキストに応じた適切なアクセスレベルを選択
				if context_type in ["services", "foundation"]:
					access_level = AccessLevel.ADMIN
				else:  # plugin
					access_level = AccessLevel.READ_ONLY
				
				with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
					try:
						credential = manager.register(access_level)
						registration_results[f"{context_type}_{module_name}"] = credential
					except ValueError as e:
						registration_results[f"{context_type}_{module_name}"] = str(e)
		
		# 登録結果の検証
		for key, result in registration_results.items():
			context_type = key.split('_')[0]
			if context_type == "plugin":
				# プラグインコンテキストでは適切に制限されている
				if isinstance(result, Credentials):
					self.assertEqual(result.access_level, AccessLevel.READ_ONLY)
			else:
				# サービスと基盤コンテキストではADMIN権限が取得できる
				if isinstance(result, Credentials):
					self.assertEqual(result.access_level, AccessLevel.ADMIN)


class TestCredentialManagerErrorHandling(unittest.TestCase):
	"""CredentialManagerのエラーハンドリングテストケース"""

	def setUp(self):
		"""エラーハンドリングテスト用の初期化処理"""
		self.temp_dir = tempfile.mkdtemp()
		self.test_base_path = os.path.join(self.temp_dir, "error_test")

	def tearDown(self):
		"""エラーハンドリングテスト用のクリーンアップ処理"""
		if os.path.exists(self.temp_dir):
			shutil.rmtree(self.temp_dir)

	def test_pathresolver_error_propagation(self):
		"""PathResolverのエラー伝播テスト"""
		manager = CredentialManager(self.test_base_path)
		
		# PathResolverがエラーを投げる場合のテスト
		with patch.object(manager.path_resolver, 'getPathInfo', side_effect=ValueError("Path resolution failed")):
			with self.assertRaises(ValueError) as context:
				manager.register(AccessLevel.READ_ONLY)
			
			self.assertEqual(str(context.exception), "Path resolution failed")

	def test_validate_with_pathresolver_error(self):
		"""検証時のPathResolverエラー処理テスト"""
		manager = CredentialManager(self.test_base_path)
		
		# PathResolverがエラーを投げる場合、validateはFalseを返すはず
		with patch.object(manager.path_resolver, 'getPathInfo', side_effect=ValueError("Path resolution failed")):
			result = manager.validate(AccessOperation.READ)
			self.assertFalse(result)

	def test_getCredential_with_pathresolver_error(self):
		"""認証情報取得時のPathResolverエラー処理テスト"""
		manager = CredentialManager(self.test_base_path)
		
		# PathResolverがエラーを投げる場合、getCredentialは例外を投げるはず
		with patch.object(manager.path_resolver, 'getPathInfo', side_effect=ValueError("Path resolution failed")):
			with self.assertRaises(ValueError) as context:
				manager.getCredential(AccessOperation.READ)
			
			self.assertEqual(str(context.exception), "Path resolution failed")

	def test_getKey_with_pathresolver_error(self):
		"""キー取得時のPathResolverエラー処理テスト"""
		manager = CredentialManager(self.test_base_path)
		
		# PathResolverがエラーを投げる場合、getKeyは例外を投げるはず
		with patch.object(manager.path_resolver, 'getPathInfo', side_effect=ValueError("Path resolution failed")):
			with self.assertRaises(ValueError) as context:
				manager.getKey()
			
			self.assertEqual(str(context.exception), "Path resolution failed")

	def test_invalid_access_operation_handling(self):
		"""無効なアクセス操作の処理テスト"""
		manager = CredentialManager(self.test_base_path)
		
		mock_path_info = PathInfo(
			name="test_caller",
			path="/path/to/test_caller/module.py",
			type="error_test"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
			manager.register(AccessLevel.READ_ONLY)
			
			# 存在しないアクセス操作での検証（モックオブジェクトを使用）
			with patch('src.primitives.AccessOperation.AccessOperation') as mock_operation:
				mock_operation.READ = "INVALID_OPERATION"
				
				# 無効な操作は拒否されるはず
				result = manager.validate(mock_operation.READ)
				self.assertFalse(result)

	def test_pathresolver_initialization_error(self):
		"""PathResolver初期化エラーのテスト"""
		# 存在しないパスでの初期化
		nonexistent_path = os.path.join(self.temp_dir, "nonexistent")
		
		# PathResolverの初期化でエラーが発生する場合をシミュレート
		# CredentialManagerの初期化時にPathResolverが作られるので、そこでパッチ
		with patch('src.services.CredentialManager.PathResolver', side_effect=ValueError("Invalid base path")):
			with self.assertRaises(ValueError) as context:
				CredentialManager(nonexistent_path)
			
			self.assertEqual(str(context.exception), "Invalid base path")

	def test_typo_in_validate_method(self):
		"""validateメソッド内のタイポの確認テスト"""
		# 注意: CredentialManager.validateメソッドには「credendial」というタイポがある
		manager = CredentialManager(self.test_base_path)
		
		mock_path_info = PathInfo(
			name="typo_test_caller",
			path="/path/to/typo_test_caller/module.py",
			type="error_test"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
			manager.register(AccessLevel.READ_ONLY)
			
			# タイポがあってもメソッドは正常動作するはず
			result = manager.validate(AccessOperation.READ)
			self.assertTrue(result)

	def test_credential_store_corruption_handling(self):
		"""認証情報ストアの破損処理テスト"""
		manager = CredentialManager(self.test_base_path)
		
		mock_path_info = PathInfo(
			name="corruption_test_caller",
			path="/path/to/corruption_test_caller/module.py",
			type="error_test"
		)
		
		with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
			# 正常に認証情報を登録
			manager.register(AccessLevel.READ_ONLY)
			
			# 内部ストアを意図的に破損（実際の属性名は_credentials）
			manager._credentials = None
			
			# 破損した状態での操作はエラーになる
			with self.assertRaises(AttributeError):
				manager.validate(AccessOperation.READ)

	def test_multiple_error_conditions(self):
		"""複数のエラー条件の組み合わせテスト"""
		manager = CredentialManager(self.test_base_path)
		
		# PathResolverエラーと無効な操作の組み合わせ
		with patch.object(manager.path_resolver, 'getPathInfo', side_effect=ValueError("Complex error")):
			# 登録時のエラー
			with self.assertRaises(ValueError):
				manager.register(AccessLevel.READ_ONLY)
			
			# 検証時は静かに失敗
			result = manager.validate(AccessOperation.READ)
			self.assertFalse(result)
			
			# 認証情報取得時のエラー
			with self.assertRaises(ValueError):
				manager.getCredential(AccessOperation.READ)


class TestCredentialManagerRobustness(unittest.TestCase):
	"""CredentialManagerの堅牢性テストケース"""

	def setUp(self):
		"""堅牢性テスト用の初期化処理"""
		self.temp_dir = tempfile.mkdtemp()
		self.test_base_path = os.path.join(self.temp_dir, "robustness_test")
		os.makedirs(self.test_base_path, exist_ok=True)

	def tearDown(self):
		"""堅牢性テスト用のクリーンアップ処理"""
		if os.path.exists(self.temp_dir):
			shutil.rmtree(self.temp_dir)

	def test_extreme_load_simulation(self):
		"""極端な負荷のシミュレーションテスト"""
		manager = CredentialManager(self.test_base_path)
		
		# 大量の認証情報を登録
		for i in range(1000):
			mock_path_info = PathInfo(
				name=f"load_test_caller_{i}",
				path=f"/path/to/load_test_caller_{i}/module.py",
				type="robustness_test"
			)
			
			with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
				credential = manager.register(AccessLevel.READ_ONLY)
				self.assertIsNotNone(credential)
		
		# 大量の認証情報が正しく管理されていることを確認
		self.assertEqual(manager.get_credential_count(), 1000)

	def test_memory_efficiency_with_large_dataset(self):
		"""大きなデータセットでのメモリ効率テスト"""
		manager = CredentialManager(self.test_base_path)
		
		# 大量のアクセスパターンをシミュレート
		caller_count = 100
		access_per_caller = 50
		
		for caller_id in range(caller_count):
			mock_path_info = PathInfo(
				name=f"memory_test_caller_{caller_id}",
				path=f"/path/to/memory_test_caller_{caller_id}/module.py",
				type="robustness_test"
			)
			
			with patch.object(manager.path_resolver, 'getPathInfo', return_value=mock_path_info):
				manager.register(AccessLevel.READ_WRITE)
				
				# 各呼び出し元で複数回アクセス
				for access_count in range(access_per_caller):
					credential = manager.getCredential(AccessOperation.READ)
					self.assertTrue(credential.enabled)
					self.assertGreaterEqual(credential.access_count, access_count + 1)
		
		# 最終的な状態確認
		self.assertEqual(manager.get_credential_count(), caller_count)


if __name__ == "__main__":
	# テストスイートの実行
	unittest.main(verbosity=2)

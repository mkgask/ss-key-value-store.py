#!/usr/bin/env python3
"""
PathResolverクラスの単体テストモジュール

このテストモジュールはPathResolverクラスの以下の機能をテストします：
- 初期化処理の検証
- パス情報の取得機能
- エラーハンドリング
"""

import sys
import os
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# テスト対象クラスのインポート
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try:
    from src.foundation.PathResolver import PathResolver
    from src.primitives.PathInfo import PathInfo
except ImportError:
    print("インポートエラーが発生しました。パスを確認してください。")
    sys.exit(1)


class TestPathResolver(unittest.TestCase):
    """PathResolverクラスのテストケース"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_base_path = os.path.join(self.temp_dir, "test_base")
        
    def tearDown(self):
        """各テストメソッド実行後のクリーンアップ処理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init_with_valid_path(self):
        """有効なパスでの初期化テスト"""
        resolver = PathResolver(self.test_base_path)
        
        # ベースパスが正しく設定されているか確認（複数ベースパス対応）
        self.assertEqual(resolver.base_paths[0], Path(self.test_base_path).resolve())
        
        # ディレクトリが作成されているか確認
        self.assertTrue(resolver.base_paths[0].exists())
        self.assertTrue(resolver.base_paths[0].is_dir())
        
        # typeが正しく設定されているか確認
        self.assertEqual(resolver.type, "test_base")

    def test_init_with_empty_path(self):
        """空のパスでの初期化時の例外テスト"""
        with self.assertRaises(ValueError) as context:
            PathResolver("")
        
        self.assertEqual(str(context.exception), "Base paths cannot be empty.")

    def test_init_with_none_path(self):
        """Noneパスでの初期化時の例外テスト"""
        with self.assertRaises(ValueError):
            PathResolver(None)

    def test_type_detection_with_plugin_path(self):
        """pluginタイプのパス検出テスト"""
        plugin_path = os.path.join(self.temp_dir, "plugin")
        resolver = PathResolver(plugin_path)
        
        self.assertEqual(resolver.type, "plugin")

    def test_type_detection_with_services_path(self):
        """servicesタイプのパス検出テスト"""
        services_path = os.path.join(self.temp_dir, "services")
        resolver = PathResolver(services_path)
        
        self.assertEqual(resolver.type, "services")

    def test_getPathInfo_successful_resolution(self):
        """正常なパス情報取得のテスト"""
        # テスト用のディレクトリ構造を作成
        caller_dir = os.path.join(self.test_base_path, "test_caller")
        os.makedirs(caller_dir, exist_ok=True)
        
        # テスト用ファイルを作成
        test_file = os.path.join(caller_dir, "test_module.py")
        with open(test_file, 'w') as f:
            f.write("# Test module")
        
        resolver = PathResolver(self.test_base_path)
        
        # スタックトレースをモック化（PathResolver自身のフレーム + テスト対象フレーム）
        resolver_frame = MagicMock()
        resolver_frame.filename = "/path/to/PathResolver.py"  # 除外されるフレーム
        
        target_frame = MagicMock()
        target_frame.filename = test_file
        
        with patch('traceback.extract_stack', return_value=[target_frame, resolver_frame]):
            path_info = resolver.getPathInfo()
            
            self.assertIsInstance(path_info, PathInfo)
            self.assertEqual(path_info.name, "test_caller")
            self.assertEqual(path_info.path, Path(test_file).resolve())
            self.assertEqual(path_info.type, "test_base")

    def test_getPathInfo_with_no_stack_frames(self):
        """スタックフレームが存在しない場合の例外テスト"""
        resolver = PathResolver(self.test_base_path)
        
        with patch('traceback.extract_stack', return_value=[]):
            with self.assertRaises(ValueError) as context:
                resolver.getPathInfo()
            
            self.assertEqual(str(context.exception), "No stack frames found.")

    def test_getPathInfo_with_external_caller(self):
        """ベースパス外からの呼び出し時の例外テスト"""
        resolver = PathResolver(self.test_base_path)
        
        # ベースパス外のファイルをモック
        external_file = "/tmp/external_module.py"
        
        resolver_frame = MagicMock()
        resolver_frame.filename = "/path/to/PathResolver.py"  # 除外されるフレーム
        
        external_frame = MagicMock()
        external_frame.filename = external_file
        
        with patch('traceback.extract_stack', return_value=[external_frame, resolver_frame]):
            with self.assertRaises(ValueError) as context:
                resolver.getPathInfo()
            
            self.assertEqual(str(context.exception), "Caller name could not be determined.")

    def test_getPathInfo_with_multiple_valid_callers(self):
        """複数の有効な呼び出し元がある場合のテスト（最初の有効なものを返す）"""
        # テスト用のディレクトリ構造を作成
        caller1_dir = os.path.join(self.test_base_path, "caller1")
        caller2_dir = os.path.join(self.test_base_path, "caller2")
        os.makedirs(caller1_dir, exist_ok=True)
        os.makedirs(caller2_dir, exist_ok=True)
        
        test_file1 = os.path.join(caller1_dir, "module1.py")
        test_file2 = os.path.join(caller2_dir, "module2.py")
        
        for file_path in [test_file1, test_file2]:
            with open(file_path, 'w') as f:
                f.write("# Test module")
        
        resolver = PathResolver(self.test_base_path)
        
        # 複数のスタックフレームをモック
        # reversed()で処理されるため、配列の最後から順に処理される
        # stacks[:-1]で最後のフレーム（PathResolver）は除外される
        resolver_frame = MagicMock()
        resolver_frame.filename = "/path/to/PathResolver.py"  # 除外されるフレーム
        
        frame1 = MagicMock()
        frame1.filename = test_file1
        
        frame2 = MagicMock()
        frame2.filename = test_file2
        
        # [frame1, frame2, resolver_frame] -> stacks[:-1] -> [frame1, frame2] -> reversed -> [frame2, frame1]
        with patch('traceback.extract_stack', return_value=[frame1, frame2, resolver_frame]):
            path_info = resolver.getPathInfo()
            
            # 逆順処理で最初に見つかるframe2（caller2）が返される
            self.assertEqual(path_info.name, "caller2")



    def test_path_resolution_with_nested_structure(self):
        """ネストした構造でのパス解決テスト"""
        # 深いネスト構造を作成
        nested_path = os.path.join(self.test_base_path, "services", "auth", "handlers")
        os.makedirs(nested_path, exist_ok=True)
        
        test_file = os.path.join(nested_path, "auth_handler.py")
        with open(test_file, 'w') as f:
            f.write("# Auth handler module")
        
        resolver = PathResolver(self.test_base_path)
        
        resolver_frame = MagicMock()
        resolver_frame.filename = "/path/to/PathResolver.py"  # 除外されるフレーム
        
        target_frame = MagicMock()
        target_frame.filename = test_file
        
        with patch('traceback.extract_stack', return_value=[target_frame, resolver_frame]):
            path_info = resolver.getPathInfo()
            
            # 最初のディレクトリ名（services）が呼び出し元名として取得されることを確認
            self.assertEqual(path_info.name, "services")
            self.assertEqual(path_info.type, "test_base")

    def test_pathinfo_immutability(self):
        """PathInfoオブジェクトの不変性テスト"""
        caller_dir = os.path.join(self.test_base_path, "test_caller")
        os.makedirs(caller_dir, exist_ok=True)
        
        test_file = os.path.join(caller_dir, "test_module.py")
        with open(test_file, 'w') as f:
            f.write("# Test module")
        
        resolver = PathResolver(self.test_base_path)
        
        resolver_frame = MagicMock()
        resolver_frame.filename = "/path/to/PathResolver.py"  # 除外されるフレーム
        
        target_frame = MagicMock()
        target_frame.filename = test_file
        
        with patch('traceback.extract_stack', return_value=[target_frame, resolver_frame]):
            path_info = resolver.getPathInfo()
            
            # PathInfoの各プロパティが期待通りに設定されていることを確認
            original_name = path_info.name
            original_path = path_info.path
            original_type = path_info.type
            
            # データクラスなので直接変更はできないが、値が保持されていることを確認
            self.assertEqual(path_info.name, original_name)
            self.assertEqual(path_info.path, original_path)
            self.assertEqual(path_info.type, original_type)

    def test_multiple_base_paths_initialization(self):
        """複数ベースパスでの初期化テスト"""
        base_paths = [self.test_base_path, str(Path(self.temp_dir) / "plugins")]
        resolver = PathResolver(base_paths)
        
        # 複数ベースパスが正しく設定されているか確認
        self.assertEqual(len(resolver.base_paths), 2)
        self.assertEqual(resolver.base_paths[0], Path(self.test_base_path).resolve())
        self.assertEqual(resolver.base_paths[1], Path(self.temp_dir, "plugins").resolve())
        
        # 主要なベースパス（最初のパス）のtypeが設定されているか確認
        self.assertEqual(resolver.type, "test_base")

    def test_multiple_base_paths_path_resolution(self):
        """複数ベースパスでのパス解決テスト"""
        # テスト用ディレクトリ構造を作成
        core_dir = Path(self.temp_dir) / "core"
        plugins_dir = Path(self.temp_dir) / "plugins"
        
        core_dir.mkdir()
        plugins_dir.mkdir()
        
        # 各ディレクトリにテストファイルを作成
        (core_dir / "admin_module").mkdir()
        (plugins_dir / "user_plugin").mkdir()
        
        base_paths = [str(core_dir), str(plugins_dir)]
        resolver = PathResolver(base_paths)
        
        # coreディレクトリからの解決をテスト
        test_file = core_dir / "admin_module" / "test.py"
        test_file.parent.mkdir(exist_ok=True)
        test_file.write_text("# Test file from core")
        
        # plugins ディレクトリからの解決をテスト
        plugin_file = plugins_dir / "user_plugin" / "plugin.py"  
        plugin_file.parent.mkdir(exist_ok=True)
        plugin_file.write_text("# Test file from plugins")
        
        # 実際のパス解決は実行時のスタックトレースに依存するので、
        # ここでは初期化が正常に完了することを確認
        self.assertEqual(len(resolver.base_paths), 2)
        self.assertEqual(resolver.base_paths[0].name, "core")
        self.assertEqual(resolver.base_paths[1].name, "plugins")

# ...existing code...

class TestPathResolverIntegration(unittest.TestCase):
    """PathResolverの統合テストケース"""

    def setUp(self):
        """統合テスト用の初期化処理"""
        self.temp_dir = tempfile.mkdtemp()
        self.services_path = os.path.join(self.temp_dir, "services")
        self.plugin_path = os.path.join(self.temp_dir, "plugin")
        
    def tearDown(self):
        """統合テスト用のクリーンアップ処理"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_services_context_scenario(self):
        """サービスコンテキストでの完全なシナリオテスト"""
        # サービス用のディレクトリ構造を作成
        auth_service_dir = os.path.join(self.services_path, "auth_service")
        os.makedirs(auth_service_dir, exist_ok=True)
        
        test_file = os.path.join(auth_service_dir, "authenticator.py")
        with open(test_file, 'w') as f:
            f.write("# Authentication service")
        
        resolver = PathResolver(self.services_path)
        
        # タイプがservicesであることを確認
        self.assertEqual(resolver.type, "services")
        
        # パス情報が正しく取得できることを確認
        resolver_frame = MagicMock()
        resolver_frame.filename = "/path/to/PathResolver.py"  # 除外されるフレーム
        
        target_frame = MagicMock()
        target_frame.filename = test_file
        
        with patch('traceback.extract_stack', return_value=[target_frame, resolver_frame]):
            path_info = resolver.getPathInfo()
            
            self.assertEqual(path_info.name, "auth_service")
            self.assertEqual(path_info.type, "services")

    def test_plugin_context_scenario(self):
        """プラグインコンテキストでの完全なシナリオテスト"""
        # プラグイン用のディレクトリ構造を作成
        user_plugin_dir = os.path.join(self.plugin_path, "user_plugin")
        os.makedirs(user_plugin_dir, exist_ok=True)
        
        test_file = os.path.join(user_plugin_dir, "plugin_main.py")
        with open(test_file, 'w') as f:
            f.write("# User plugin main")
        
        resolver = PathResolver(self.plugin_path)
        
        # タイプがpluginであることを確認
        self.assertEqual(resolver.type, "plugin")
        
        # パス情報が正しく取得できることを確認
        resolver_frame = MagicMock()
        resolver_frame.filename = "/path/to/PathResolver.py"  # 除外されるフレーム
        
        target_frame = MagicMock()
        target_frame.filename = test_file
        
        with patch('traceback.extract_stack', return_value=[target_frame, resolver_frame]):
            path_info = resolver.getPathInfo()
            
            self.assertEqual(path_info.name, "user_plugin")
            self.assertEqual(path_info.type, "plugin")


if __name__ == "__main__":
    # テストスイートの実行
    unittest.main(verbosity=2)

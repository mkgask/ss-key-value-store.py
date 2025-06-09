#!/usr/bin/env python3
"""
セキュリティ昇格防止のテストケース
複数ベースパスでのADMIN権限昇格が正しく制御されるかテスト
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.foundation.PathResolver import PathResolver
from src.services.CredentialManager import CredentialManager
from src.primitives.AccessLevel import AccessLevel


class TestSecurityEscalation(unittest.TestCase):
    """セキュリティ昇格防止のテストクラス"""
    
    def setUp(self):
        """テスト用の一時ディレクトリを作成"""
        self.temp_dir = tempfile.mkdtemp()
        
        # core/, plugins/, engines/ ディレクトリを作成
        self.core_dir = Path(self.temp_dir) / "core"
        self.plugins_dir = Path(self.temp_dir) / "plugins"
        self.engines_dir = Path(self.temp_dir) / "engines"
        
        self.core_dir.mkdir()
        self.plugins_dir.mkdir()
        self.engines_dir.mkdir()
        
        # 各ディレクトリにサブディレクトリを作成
        (self.core_dir / "admin_module").mkdir()
        (self.plugins_dir / "user_plugin").mkdir()
        (self.engines_dir / "data_engine").mkdir()
        
        # ベースパスリスト
        self.base_paths = [str(self.core_dir), str(self.plugins_dir), str(self.engines_dir)]
    
    def tearDown(self):
        """テスト用ディレクトリをクリーンアップ"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_core_admin_escalation_allowed(self):
        """core/からのADMIN権限昇格が許可されることをテスト"""
        # core/admin_module ディレクトリに移動
        original_cwd = os.getcwd()
        test_file = self.core_dir / "admin_module" / "test_admin.py"
        test_file.write_text("# Core admin test file")
        
        try:
            os.chdir(self.core_dir / "admin_module")
            
            # CredentialManagerを作成
            credentials_manager = CredentialManager(self.base_paths)
            
            # PathInfoを取得
            pathinfo = credentials_manager.path_resolver.getPathInfo()
            
            # core からの呼び出しであることを確認
            self.assertEqual(pathinfo.type, "core")
            self.assertEqual(pathinfo.name, "admin_module")
            
            # ADMIN昇格が許可されることを確認
            can_escalate = credentials_manager.canEscalateToAdmin(pathinfo)
            self.assertTrue(can_escalate, "core/からのADMIN昇格が許可されるべき")
            
            # 実際にADMIN権限で登録できることを確認
            credential = credentials_manager.register(AccessLevel.ADMIN)
            self.assertEqual(credential.access_level, AccessLevel.ADMIN)
            
        finally:
            os.chdir(original_cwd)
    
    def test_plugins_admin_escalation_blocked(self):
        """plugins/からのADMIN権限昇格が拒否されることをテスト"""
        # plugins/user_plugin ディレクトリに移動
        original_cwd = os.getcwd()
        test_file = self.plugins_dir / "user_plugin" / "test_plugin.py"
        test_file.write_text("# Plugin test file")
        
        try:
            os.chdir(self.plugins_dir / "user_plugin")
            
            # CredentialManagerを作成
            credentials_manager = CredentialManager(self.base_paths)
            
            # PathInfoを取得
            pathinfo = credentials_manager.path_resolver.getPathInfo()
            
            # plugins からの呼び出しであることを確認
            self.assertEqual(pathinfo.type, "plugins")
            self.assertEqual(pathinfo.name, "user_plugin")
            
            # ADMIN昇格が拒否されることを確認
            can_escalate = credentials_manager.canEscalateToAdmin(pathinfo)
            self.assertFalse(can_escalate, "plugins/からのADMIN昇格は拒否されるべき")
            
            # ADMIN権限での登録が失敗することを確認
            with self.assertRaises(ValueError) as context:
                credentials_manager.register(AccessLevel.ADMIN)
            
            self.assertIn("Admin access level is not allowed", str(context.exception))
            
        finally:
            os.chdir(original_cwd)
    
    def test_engines_admin_escalation_allowed(self):
        """engines/からのADMIN権限昇格が許可されることをテスト"""
        # engines/data_engine ディレクトリに移動
        original_cwd = os.getcwd()
        test_file = self.engines_dir / "data_engine" / "test_engine.py"
        test_file.write_text("# Engine test file")
        
        try:
            os.chdir(self.engines_dir / "data_engine")
            
            # CredentialManagerを作成
            credentials_manager = CredentialManager(self.base_paths)
            
            # PathInfoを取得
            pathinfo = credentials_manager.path_resolver.getPathInfo()
            
            # engines からの呼び出しであることを確認
            self.assertEqual(pathinfo.type, "engines")
            self.assertEqual(pathinfo.name, "data_engine")
            
            # ADMIN昇格が許可されることを確認
            can_escalate = credentials_manager.canEscalateToAdmin(pathinfo)
            self.assertTrue(can_escalate, "engines/からのADMIN昇格が許可されるべき")
            
            # 実際にADMIN権限で登録できることを確認
            credential = credentials_manager.register(AccessLevel.ADMIN)
            self.assertEqual(credential.access_level, AccessLevel.ADMIN)
            
        finally:
            os.chdir(original_cwd)
    
    def test_path_resolution_priority(self):
        """パス解決の優先度が正しく動作することをテスト"""
        # より深い階層のパスが優先されることをテスト
        deeper_core_dir = self.core_dir / "subdir" / "admin_module"
        deeper_core_dir.mkdir(parents=True)
        
        # より深いベースパスを追加
        deeper_base_paths = self.base_paths + [str(self.core_dir / "subdir")]
        
        original_cwd = os.getcwd()
        test_file = deeper_core_dir / "test_deep.py"
        test_file.write_text("# Deep core test file")
        
        try:
            os.chdir(deeper_core_dir)
            
            # CredentialManagerを作成（より深いベースパスを含む）
            credentials_manager = CredentialManager(deeper_base_paths)
            
            # PathInfoを取得
            pathinfo = credentials_manager.path_resolver.getPathInfo()
            
            # より具体的（深い）パスが選択されることを確認
            self.assertEqual(pathinfo.name, "admin_module")
            # より深い階層のベースパスのtypeが選択される
            self.assertEqual(pathinfo.type, "subdir")
            
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main(verbosity=2)

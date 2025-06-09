#!/usr/bin/env python3
"""
PathResolver の複数ベースパス動作テスト
"""
import tempfile
import os
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.foundation.PathResolver import PathResolver
from src.services.CredentialManager import CredentialManager
from src.primitives.AccessLevel import AccessLevel

def test_path_resolution():
    """PathResolverの複数ベースパス動作をテスト"""
    print("🔍 PathResolver 複数ベースパス動作テスト")
    print("=" * 50)
    
    # テスト用ディレクトリ作成
    temp_dir = tempfile.mkdtemp()
    print(f"テスト環境: {temp_dir}")
    
    core_dir = Path(temp_dir) / "core"
    plugins_dir = Path(temp_dir) / "plugins"
    
    core_dir.mkdir()
    plugins_dir.mkdir()
    
    # テストファイル作成
    core_test_file = core_dir / "test_core.py"
    plugins_test_file = plugins_dir / "test_plugin.py"
    
    core_test_file.write_text("# Core test file")
    plugins_test_file.write_text("# Plugin test file")
    
    # 複数ベースパスでPathResolverを作成
    base_paths = [str(core_dir), str(plugins_dir)]
    path_resolver = PathResolver(base_paths)
    
    print(f"ベースパス: {base_paths}")
    
    # Core/からの呼び出しをシミュレート
    original_cwd = os.getcwd()
    
    try:
        print("\n1️⃣ Core/からの呼び出し:")
        os.chdir(core_dir)
        
        # CredentialManagerを作成して権限昇格をテスト
        credentials_manager = CredentialManager(base_paths)
        pathinfo = credentials_manager.path_resolver.getPathInfo()
        
        print(f"   name: {pathinfo.name}")
        print(f"   path: {pathinfo.path}")
        print(f"   type: {pathinfo.type}")
        
        # ADMIN昇格テスト
        can_escalate = credentials_manager.canEscalateToAdmin(pathinfo)
        print(f"   ADMIN昇格可能: {can_escalate}")
        
        if can_escalate:
            try:
                credential = credentials_manager.register(AccessLevel.ADMIN)
                print(f"   ✅ ADMIN登録成功: {credential.access_level}")
            except ValueError as e:
                print(f"   ❌ ADMIN登録失敗: {e}")
        
        print("\n2️⃣ Plugins/からの呼び出し:")
        os.chdir(plugins_dir)
        
        # 新しいCredentialManagerを作成（plugins/から）
        plugins_credentials_manager = CredentialManager(base_paths)
        plugins_pathinfo = plugins_credentials_manager.path_resolver.getPathInfo()
        
        print(f"   name: {plugins_pathinfo.name}")
        print(f"   path: {plugins_pathinfo.path}")
        print(f"   type: {plugins_pathinfo.type}")
        
        # ADMIN昇格テスト
        plugins_can_escalate = plugins_credentials_manager.canEscalateToAdmin(plugins_pathinfo)
        print(f"   ADMIN昇格可能: {plugins_can_escalate}")
        
        if plugins_can_escalate:
            try:
                plugins_credential = plugins_credentials_manager.register(AccessLevel.ADMIN)
                print(f"   ❌ ADMIN登録成功 (セキュリティ問題!): {plugins_credential.access_level}")
            except ValueError as e:
                print(f"   ✅ ADMIN登録ブロック: {e}")
        else:
            print(f"   ✅ ADMIN昇格が正しくブロックされました")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        os.chdir(original_cwd)
        # クリーンアップ
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    test_path_resolution()

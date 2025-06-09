#!/usr/bin/env python3
"""
複数ベースパスでのADMIN権限昇格テスト
plugins/からADMIN権限に昇格できないことを確認
"""

import os
import tempfile
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# テスト用ディレクトリ構造を作成
def setup_test_directories():
    """テスト用のディレクトリ構造を作成"""
    temp_dir = Path(tempfile.mkdtemp())
    
    # ディレクトリ構造を作成
    core_dir = temp_dir / "core"
    plugins_dir = temp_dir / "plugins"
    engines_dir = temp_dir / "engines"
    
    core_dir.mkdir(parents=True, exist_ok=True)
    plugins_dir.mkdir(parents=True, exist_ok=True)  
    engines_dir.mkdir(parents=True, exist_ok=True)
    
    # テスト用ファイルを作成
    core_test_file = core_dir / "core_module.py"
    plugin_test_file = plugins_dir / "test_plugin.py"
    engine_test_file = engines_dir / "test_engine.py"
    
    core_test_file.write_text("""
import sys
sys.path.insert(0, '/mnt/g/projects/silver-star/ss-key-value-store.py/src')

from services.CredentialManager import CredentialManager
from primitives.AccessLevel import AccessLevel

def test_admin_escalation_from_core():
    \"\"\"core/からのADMIN権限昇格テスト\"\"\"
    base_paths = ['/mnt/g/projects/silver-star/ss-key-value-store.py/test_temp_core/core',
                  '/mnt/g/projects/silver-star/ss-key-value-store.py/test_temp_core/plugins',
                  '/mnt/g/projects/silver-star/ss-key-value-store.py/test_temp_core/engines']
    
    credential_manager = CredentialManager(base_paths)
    
    try:
        # core/からADMIN権限で登録を試行
        credential = credential_manager.register(AccessLevel.ADMIN)
        print(f"✅ Core: ADMIN権限での登録成功 - {credential.name} ({credential.access_level})")
        return True
    except ValueError as e:
        print(f"❌ Core: ADMIN権限での登録失敗 - {e}")
        return False

if __name__ == "__main__":
    test_admin_escalation_from_core()
""")
    
    plugin_test_file.write_text("""
import sys
sys.path.insert(0, '/mnt/g/projects/silver-star/ss-key-value-store.py/src')

from services.CredentialManager import CredentialManager
from primitives.AccessLevel import AccessLevel

def test_admin_escalation_from_plugin():
    \"\"\"plugins/からのADMIN権限昇格テスト\"\"\"
    base_paths = ['/mnt/g/projects/silver-star/ss-key-value-store.py/test_temp_core/core',
                  '/mnt/g/projects/silver-star/ss-key-value-store.py/test_temp_core/plugins',
                  '/mnt/g/projects/silver-star/ss-key-value-store.py/test_temp_core/engines']
    
    credential_manager = CredentialManager(base_paths)
    
    try:
        # plugins/からADMIN権限で登録を試行
        credential = credential_manager.register(AccessLevel.ADMIN)
        print(f"⚠️  Plugin: ADMIN権限での登録成功（これは問題！） - {credential.name} ({credential.access_level})")
        return True
    except ValueError as e:
        print(f"✅ Plugin: ADMIN権限での登録失敗（期待通り） - {e}")
        return False

if __name__ == "__main__":
    test_admin_escalation_from_plugin()
""")
    
    engine_test_file.write_text("""
import sys
sys.path.insert(0, '/mnt/g/projects/silver-star/ss-key-value-store.py/src')

from services.CredentialManager import CredentialManager
from primitives.AccessLevel import AccessLevel

def test_admin_escalation_from_engine():
    \"\"\"engines/からのADMIN権限昇格テスト\"\"\"
    base_paths = ['/mnt/g/projects/silver-star/ss-key-value-store.py/test_temp_core/core',
                  '/mnt/g/projects/silver-star/ss-key-value-store.py/test_temp_core/plugins',
                  '/mnt/g/projects/silver-star/ss-key-value-store.py/test_temp_core/engines']
    
    credential_manager = CredentialManager(base_paths)
    
    try:
        # engines/からADMIN権限で登録を試行
        credential = credential_manager.register(AccessLevel.ADMIN)
        print(f"✅ Engine: ADMIN権限での登録成功 - {credential.name} ({credential.access_level})")
        return True
    except ValueError as e:
        print(f"❌ Engine: ADMIN権限での登録失敗 - {e}")
        return False

if __name__ == "__main__":
    test_admin_escalation_from_engine()
""")
    
    return temp_dir, core_test_file, plugin_test_file, engine_test_file

def main():
    """メインテスト実行"""
    print("🧪 複数ベースパスでのADMIN権限昇格テストを開始...")
    
    # テスト環境セットアップ
    temp_dir, core_file, plugin_file, engine_file = setup_test_directories()
    print(f"📁 テスト用ディレクトリ: {temp_dir}")
    
    try:
        # 各ディレクトリに名前を変更（実際のパスを使用）
        actual_temp_dir = Path("/mnt/g/projects/silver-star/ss-key-value-store.py/test_temp_core")
        if actual_temp_dir.exists():
            import shutil
            shutil.rmtree(actual_temp_dir)
        
        shutil.copytree(temp_dir, actual_temp_dir)
        
        print("\n1️⃣ core/からのADMIN権限昇格テスト:")
        os.system(f"cd {actual_temp_dir}/core && python core_module.py")
        
        print("\n2️⃣ plugins/からのADMIN権限昇格テスト:")
        os.system(f"cd {actual_temp_dir}/plugins && python test_plugin.py")
        
        print("\n3️⃣ engines/からのADMIN権限昇格テスト:")
        os.system(f"cd {actual_temp_dir}/engines && python test_engine.py")
        
    finally:
        # クリーンアップ
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if Path("/mnt/g/projects/silver-star/ss-key-value-store.py/test_temp_core").exists():
            shutil.rmtree("/mnt/g/projects/silver-star/ss-key-value-store.py/test_temp_core")

if __name__ == "__main__":
    main()

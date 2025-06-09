#!/usr/bin/env python3
"""
セキュリティ昇格テスト
core/とplugins/の権限分離が正しく動作するかテスト
"""
import tempfile
import os
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# テスト用のディレクトリ構造を作成
def setup_test_environment():
    """テスト用のディレクトリ構造を作成"""
    temp_dir = tempfile.mkdtemp()
    
    # core/, plugins/, engines/ ディレクトリを作成
    core_dir = Path(temp_dir) / "core"
    plugins_dir = Path(temp_dir) / "plugins" 
    engines_dir = Path(temp_dir) / "engines"
    
    core_dir.mkdir()
    plugins_dir.mkdir()
    engines_dir.mkdir()
    
    # 各ディレクトリにテスト用モジュールを作成
    (core_dir / "__init__.py").write_text("")
    (plugins_dir / "__init__.py").write_text("")
    (engines_dir / "__init__.py").write_text("")
    
    # core/admin_module.py
    (core_dir / "admin_module.py").write_text("""
import sys
sys.path.insert(0, '/mnt/g/projects/silver-star/ss-key-value-store.py/src')

from services.CredentialManager import CredentialManager
from services.KVStore import KVStore
from primitives.AccessLevel import AccessLevel

def create_shared_store():
    # core/から複数ベースパスでKVStoreを作成
    base_paths = ['/tmp/test_env/core', '/tmp/test_env/plugins', '/tmp/test_env/engines']
    credentials_manager = CredentialManager(base_paths)
    
    # ADMIN権限で登録を試行
    try:
        credential = credentials_manager.register(AccessLevel.ADMIN)
        print(f"✅ Core ADMIN registration: SUCCESS - {credential.access_level}")
        return KVStore(credentials_manager)
    except ValueError as e:
        print(f"❌ Core ADMIN registration: FAILED - {e}")
        return None
""")
    
    # plugins/plugin_module.py
    (plugins_dir / "plugin_module.py").write_text("""
import sys
sys.path.insert(0, '/mnt/g/projects/silver-star/ss-key-value-store.py/src')

from services.CredentialManager import CredentialManager
from services.KVStore import KVStore
from primitives.AccessLevel import AccessLevel

def try_admin_escalation():
    # plugins/から複数ベースパスでKVStoreを作成
    base_paths = ['/tmp/test_env/core', '/tmp/test_env/plugins', '/tmp/test_env/engines']
    credentials_manager = CredentialManager(base_paths)
    
    # ADMIN権限で登録を試行（これは失敗すべき）
    try:
        credential = credentials_manager.register(AccessLevel.ADMIN)
        print(f"❌ Plugin ADMIN registration: SUCCESS (SECURITY BREACH!) - {credential.access_level}")
        return True
    except ValueError as e:
        print(f"✅ Plugin ADMIN registration: BLOCKED - {e}")
        return False

def use_shared_store(kvstore):
    # 共有ストアを使用（これは成功すべき）
    try:
        kvstore.shared_set("plugin_data", "test_value")
        value = kvstore.shared_get("plugin_data")
        print(f"✅ Plugin shared store access: SUCCESS - {value}")
        return True
    except Exception as e:
        print(f"❌ Plugin shared store access: FAILED - {e}")
        return False
""")
    
    return temp_dir.replace("/tmp/", "/tmp/test_env/")

def run_security_test():
    """セキュリティテストを実行"""
    print("🔒 セキュリティ昇格テスト開始")
    print("=" * 50)
    
    # テスト環境セットアップ
    test_env = setup_test_environment()
    
    # パスを更新してテスト環境を使用
    original_cwd = os.getcwd()
    
    try:
        # core/admin_module.pyを実行してADMIN権限のKVStoreを作成
        core_path = Path(test_env) / "core"
        os.chdir(core_path)
        
        sys.path.insert(0, str(core_path))
        import admin_module
        
        print("1️⃣ Core/からのADMIN権限登録テスト:")
        shared_store = admin_module.create_shared_store()
        
        if shared_store:
            print("\n2️⃣ 共有ストアにデータを設定:")
            shared_store.shared_set("global_config", "admin_value")
            shared_store.readonly_set("system_config", "readonly_value")
            print("✅ ADMIN権限での共有データ設定完了")
        
        # plugins/plugin_module.pyを実行してADMIN昇格を試行
        plugins_path = Path(test_env) / "plugins"
        os.chdir(plugins_path)
        
        sys.path.insert(0, str(plugins_path))
        import plugin_module
        
        print("\n3️⃣ Plugins/からのADMIN権限昇格試行:")
        escalation_success = plugin_module.try_admin_escalation()
        
        if shared_store:
            print("\n4️⃣ Plugin/からの共有ストアアクセス:")
            access_success = plugin_module.use_shared_store(shared_store)
        
        print("\n" + "=" * 50)
        print("🔒 セキュリティテスト結果:")
        print(f"   ADMIN昇格防止: {'✅ 成功' if not escalation_success else '❌ 失敗'}")
        print(f"   共有ストアアクセス: {'✅ 成功' if shared_store and access_success else '❌ 失敗'}")
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        os.chdir(original_cwd)
        # クリーンアップ
        import shutil
        shutil.rmtree(test_env, ignore_errors=True)

if __name__ == "__main__":
    run_security_test()

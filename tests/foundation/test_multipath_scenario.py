#!/usr/bin/env python3
"""
複数ベースパスでのKVStore動作確認テスト
実際のcore/とplugins/のシナリオをシミュレーション
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.services.CredentialManager import CredentialManager
from src.services.KVStore import KVStore
from src.primitives.AccessLevel import AccessLevel

def test_multipath_scenario():
    """複数ベースパスでのKVStore動作テスト"""
    print("🔍 複数ベースパス KVStore 動作テスト")
    print("=" * 50)
    
    # 実際のプロジェクト構造をシミュレート
    temp_dir = tempfile.mkdtemp()
    
    try:
        # core/, plugins/, engines/ ディレクトリを作成
        core_dir = Path(temp_dir) / "core"
        plugins_dir = Path(temp_dir) / "plugins"
        engines_dir = Path(temp_dir) / "engines"
        
        core_dir.mkdir()
        plugins_dir.mkdir()
        engines_dir.mkdir()
        
        # 各ディレクトリにサブディレクトリとテストファイルを作成
        (core_dir / "admin_service").mkdir()
        (plugins_dir / "user_plugin").mkdir()
        
        core_test_file = core_dir / "admin_service" / "admin.py"
        plugin_test_file = plugins_dir / "user_plugin" / "plugin.py"
        
        # Core用のテストスクリプトを作成
        core_script = f'''
import sys
sys.path.insert(0, "{project_root}")

from src.services.CredentialManager import CredentialManager
from src.services.KVStore import KVStore
from src.primitives.AccessLevel import AccessLevel

# 複数ベースパスでCredentialManagerを作成
base_paths = ["{core_dir}", "{plugins_dir}", "{engines_dir}"]
credentials_manager = CredentialManager(base_paths)

try:
    # ADMIN権限での登録を試行
    credential = credentials_manager.register(AccessLevel.ADMIN)
    print(f"✅ Core ADMIN登録成功: {{credential.access_level}}")
    print(f"   Caller: {{credential.name}}")
    print(f"   Type: {{credential.type}}")
    
    # KVStoreを作成して共有データを設定
    kvstore = KVStore(credentials_manager)
    kvstore.shared_set("global_config", "admin_value")
    kvstore.readonly_set("system_config", "readonly_value")
    print("✅ 共有ストレージへのデータ設定完了")
    
except Exception as e:
    print(f"❌ Core処理エラー: {{e}}")
    import traceback
    traceback.print_exc()
'''
        
        # Plugin用のテストスクリプトを作成
        plugin_script = f'''
import sys
sys.path.insert(0, "{project_root}")

from src.services.CredentialManager import CredentialManager
from src.services.KVStore import KVStore
from src.primitives.AccessLevel import AccessLevel

# 複数ベースパスでCredentialManagerを作成
base_paths = ["{core_dir}", "{plugins_dir}", "{engines_dir}"]
credentials_manager = CredentialManager(base_paths)

# ADMIN権限での登録を試行（これは失敗すべき）
try:
    credential = credentials_manager.register(AccessLevel.ADMIN)
    print(f"❌ Plugin ADMIN登録成功 (セキュリティ問題!): {{credential.access_level}}")
except Exception as e:
    print(f"✅ Plugin ADMIN登録ブロック: {{e}}")

# 通常権限での登録とアクセス
try:
    credential = credentials_manager.register(AccessLevel.READ_WRITE)
    print(f"✅ Plugin READ_WRITE登録成功: {{credential.access_level}}")
    print(f"   Caller: {{credential.name}}")
    print(f"   Type: {{credential.type}}")
    
    # KVStoreで共有データにアクセス
    kvstore = KVStore(credentials_manager)
    
    # 共有読み書きストレージにアクセス
    kvstore.shared_set("plugin_data", "plugin_value")
    shared_value = kvstore.shared_get("global_config", "not_found")
    print(f"✅ 共有データアクセス: {{shared_value}}")
    
    # 読み取り専用ストレージにアクセス
    readonly_value = kvstore.readonly_get("system_config", "not_found")
    print(f"✅ 読み取り専用データアクセス: {{readonly_value}}")
    
    # 読み取り専用ストレージへの書き込み試行（これは失敗すべき）
    try:
        kvstore.readonly_set("plugin_config", "should_fail")
        print("❌ Plugin による読み取り専用ストレージへの書き込み成功 (セキュリティ問題!)")
    except Exception as e:
        print(f"✅ Plugin 読み取り専用ストレージ書き込みブロック: {{e}}")
    
except Exception as e:
    print(f"❌ Plugin処理エラー: {{e}}")
    import traceback
    traceback.print_exc()
'''
        
        core_test_file.write_text(core_script)
        plugin_test_file.write_text(plugin_script)
        
        print(f"テスト環境作成: {temp_dir}")
        print(f"Core dir: {core_dir}")
        print(f"Plugins dir: {plugins_dir}")
        
        # 元の作業ディレクトリを保存
        original_cwd = os.getcwd()
        
        # Core/からの実行テスト
        print("\n1️⃣ Core/admin_service からの実行:")
        os.chdir(core_dir / "admin_service")
        os.system(f"python3 {core_test_file}")
        
        # Plugin/からの実行テスト
        print("\n2️⃣ Plugins/user_plugin からの実行:")
        os.chdir(plugins_dir / "user_plugin")
        os.system(f"python3 {plugin_test_file}")
        
        # 作業ディレクトリを元に戻す
        os.chdir(original_cwd)
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # クリーンアップ
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    test_multipath_scenario()

from src.services.CredentialManager import CredentialManager
from src.services.KVStore import KVStore
from src.primitives.AccessLevel import AccessLevel


def test_multipath_kvstore_scenario():
    """
    core/でKVStoreを作成し、plugins/から使用するシナリオのテスト
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # ディレクトリ構造を作成
        core_dir = temp_path / "core"
        engines_dir = temp_path / "engines" 
        plugins_dir = temp_path / "plugins"
        
        core_dir.mkdir()
        engines_dir.mkdir()
        plugins_dir.mkdir()
        
        # 複数ベースパス対応のCredentialManagerを作成
        credential_manager = CredentialManager([
            str(core_dir),
            str(engines_dir), 
            str(plugins_dir)
        ])
        
        # KVStoreを作成
        kvstore = KVStore(credential_manager)
        
        print("=== KVStore作成完了 ===")
        
        # core/内でのテスト用ファイルを作成
        core_test_file = core_dir / "core_service.py"
        core_test_file.write_text("""
# core/のサービスファイル
import sys
sys.path.append('/mnt/g/projects/silver-star/ss-key-value-store.py')

def test_core_kvstore_usage():
    from src.primitives.AccessLevel import AccessLevel
    # このファイルから実行すると、PathInfoのnameは'core_service'になるはず
    pass
""")
        
        # plugins/内でのテスト用ファイルを作成  
        plugin_test_file = plugins_dir / "sample_plugin.py"
        plugin_test_file.write_text("""
# plugins/のプラグインファイル
import sys
sys.path.append('/mnt/g/projects/silver-star/ss-key-value-store.py')

def test_plugin_kvstore_usage():
    from src.primitives.AccessLevel import AccessLevel
    # このファイルから実行すると、PathInfoのnameは'sample_plugin'になるはず
    pass
""")
        
        print(f"テスト環境セットアップ完了:")
        print(f"- core_dir: {core_dir}")
        print(f"- engines_dir: {engines_dir}")
        print(f"- plugins_dir: {plugins_dir}")
        
        # 各ディレクトリからの認証情報登録テスト
        print("\n=== 認証情報登録テスト ===")
        
        # このスクリプト自体はプロジェクトルートから実行されるので、
        # 各ディレクトリ内のコードを動的に実行してパスを確認
        
        return credential_manager, kvstore


if __name__ == "__main__":
    test_multipath_kvstore_scenario()

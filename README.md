# ss-key-value-store.py

パスベース認証によるセキュリティキーバリューストアライブラリ

## 概要

`ss-key-value-store.py`は、呼び出し元のパス情報に基づいてアクセス制御を行うキーバリューストアライブラリです。各モジュールは自身の認証情報に基づいて隔離されたストレージ領域を持ち、共有ストレージへのアクセスも権限により制御されます。

## 主な特徴

- **パスベース認証**: 呼び出し元のファイルパスに基づいて自動的にアクセス権限を決定
- **隔離されたストレージ**: 各モジュールは独自の専用ストレージ領域を持つ
- **多階層権限管理**: ADMIN、READ_WRITE、WRITE_ONLY、READ_ONLYの4段階のアクセスレベル
- **共有ストレージ**: 全モジュールがアクセス可能な読み書きストレージと管理者のみが書き込める読み込み専用ストレージ
- **セキュリティ境界**: core/およびengine/は管理者権限、plugins/は制限付きアクセス
- **複数ベースパス対応**: 複数のディレクトリを基準としたパス解決

## インストール

```bash
pip install -e .
```

## クイックスタート

### 基本的な使用方法

```python
from src.services.CredentialManager import CredentialManager
from src.services.KVStore import KVStore
from src.primitives.AccessLevel import AccessLevel

# CredentialManagerを初期化（単一ベースパス）
credential_manager = CredentialManager("./my_project")

# 認証情報を登録
credential_manager.register(AccessLevel.READ_WRITE)

# KVStoreを作成
kv_store = KVStore(credential_manager)

# データの操作
kv_store.set("key1", "value1")
print(kv_store.get("key1"))  # "value1"
```

### 複数ベースパスでの使用方法

```python
# 複数のディレクトリを基準とする場合
base_paths = ["./core", "./plugins", "./engines"]
credential_manager = CredentialManager(base_paths)

# 呼び出し元のパスに応じて自動的に権限が決定される
credential_manager.register(AccessLevel.ADMIN)  # core/からならADMIN、plugins/なら制限される

kv_store = KVStore(credential_manager)
```

### 共有ストレージの使用

```python
# 全ユーザーがアクセス可能な共有ストレージ
kv_store.shared_set("shared_key", "shared_value")
value = kv_store.shared_get("shared_key")

# 管理者のみが書き込み可能な読み込み専用ストレージ
try:
    kv_store.readonly_set("config_key", "config_value")  # 管理者のみ成功
except PermissionError:
    print("管理者権限が必要です")

# 全ユーザーが読み取り可能
config = kv_store.readonly_get("config_key")
```

## アーキテクチャ

### 構造図

```
KVStore
├─ CredentialManager
│   ├─ PathResolver (パス解決とアクセス制御)
│   └─ ProtectedStore (認証情報の安全な保存)
├─ ProtectedStore (呼び出し元別の隔離されたストレージ)
├─ Shared ReadWrite Store (共有読み書きストレージ)
└─ Shared ReadOnly Store (共有読み込み専用ストレージ)
```

## セキュリティ機能

### パスベースアクセス制御

- **core/**: ADMIN権限での登録が可能
- **engines/**: ADMIN権限での登録が可能
- **plugin/**: READ_ONLY権限に制限

### 隔離されたストレージ

各呼び出し元は独自のProtectedStoreを持ち、他のモジュールからはアクセスできません。

### 共有ストレージのアクセス制御

- **読み書きストレージ**: 全ユーザーがアクセス可能
- **読み込み専用ストレージ**: 読み取りは全ユーザー、書き込みは管理者のみ

## 開発とテスト

### テストの実行

```bash
# 全テストを実行
python -m pytest

# 特定のテストカテゴリを実行
python -m pytest tests/services/
python -m pytest tests/security/
python -m pytest tests/foundation/
```

### テストカバレッジ

- **基本機能テスト**: KVStoreの基本的なCRUD操作
- **セキュリティテスト**: 権限昇格の防止、アクセス制御
- **統合テスト**: 複数コンポーネント間の連携
- **エラーハンドリングテスト**: 異常系の動作確認

## ライセンス

MIT License

## セキュリティ制限と注意事項

### Pythonの言語仕様による制約

**⚠️ 重要な制限事項**

- **リフレクション攻撃への脆弱性**: Pythonの仕様により、リフレクション攻撃を完全に防御することはできません
- **動的コード実行**: `getattr()`、`setattr()`等を使用した動的アクセスは検出・防止が困難です
- **スタックフレーム操作**: `traceback`モジュールや`inspect`モジュールを悪用したスタックフレーム偽装の可能性があります
- **モジュールインポート攻撃**: 悪意のあるモジュールによる`sys.modules`操作や`__import__`フックの悪用
- **ガベージコレクション経由のアクセス**: `gc`モジュールを通じたオブジェクト参照の取得

### 対策と推奨事項

**基本的な対策**

- **信頼できる実行環境**: このライブラリは信頼できるコード環境でのみ使用してください
- **コードレビュー**: 全てのコードに対して厳格なセキュリティレビューを実施してください
- **サンドボックス化**: 可能な限り、制限された実行環境（Docker、仮想環境等）で使用してください
- **モニタリング**: 異常なアクセスパターンや予期しない動作を監視してください

**追加のセキュリティ層**

- **ファイルシステムレベルの権限制御**: OSレベルでのファイルアクセス制御を併用してください
- **ネットワークセグメンテーション**: 重要なデータへのアクセスをネットワークレベルで制限してください
- **暗号化**: 機密データは暗号化して保存してください
- **監査ログ**: 全てのアクセスを記録し、定期的に監査してください
- **プロダクション環境**: 十分なセキュリティテストと追加の保護措置を実施した上で使用してください
- **定期的な見直し**: セキュリティ設定とアクセス権限を定期的に見直してください
- **最新化**: セキュリティパッチや更新を定期的に適用してください

**このライブラリは「多層防御の一部」として位置づけ、単独でのセキュリティに依存しないでください。**



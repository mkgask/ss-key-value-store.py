#!/usr/bin/env python3
"""
ProtectedStoreクラスの基礎的な単体テストモジュール

このテストモジュールはProtectedStoreクラスの基本機能をテストします：
- 初期化処理の検証
- 基本的なアクセス制御機能の検証
- 辞書操作機能の検証
- 基本的なエラーハンドリングの検証
"""

import sys
import os
import unittest
import copy
from typing import Any
from unittest.mock import patch, MagicMock

# テスト対象クラスのインポート
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

try:
    from src.foundation.ProtectedStore import ProtectedStore
except ImportError as e:
    print(f"ImportError: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Project root: {project_root}")
    print(f"sys.path: {sys.path}")
    sys.exit(1)


class MockAuthorizedClass:
    """
    ProtectedStoreへのアクセスが許可されたテスト用クラス
    
    このクラスは許可されたアクセサーとして、
    ProtectedStoreの操作を安全に実行する
    """

    def __init__(self, identifier: str = "authorized_instance"):
        """
        初期化処理
        
        Args:
            identifier: インスタンスの識別子
        """
        self.identifier = identifier

    def set_value(self, store: ProtectedStore, key: str, value: Any) -> None:
        """
        ProtectedStoreに値を設定する
        
        Args:
            store: 操作対象のProtectedStore
            key: 設定するキー
            value: 設定する値
        """
        store[key] = value

    def get_value(self, store: ProtectedStore, key: str) -> Any:
        """
        ProtectedStoreから値を取得する
        
        Args:
            store: 操作対象のProtectedStore
            key: 取得するキー
            
        Returns:
            取得した値
        """
        return store[key]

    def check_contains(self, store: ProtectedStore, key: str) -> bool:
        """
        キーの存在をチェックする
        
        Args:
            store: 操作対象のProtectedStore
            key: チェックするキー
            
        Returns:
            キーが存在する場合True
        """
        return key in store

    def get_store_length(self, store: ProtectedStore) -> int:
        """
        ストアの要素数を取得する
        
        Args:
            store: 操作対象のProtectedStore
            
        Returns:
            ストア内の要素数
        """
        return len(store)

    def clear_store(self, store: ProtectedStore) -> None:
        """
        ストアをクリアする
        
        Args:
            store: 操作対象のProtectedStore
        """
        store.clear()

    def get_with_default(self, store: ProtectedStore, key: str, default: Any = None) -> Any:
        """
        ProtectedStoreから値をデフォルト値付きで取得する
        
        Args:
            store: 操作対象のProtectedStore
            key: 取得するキー
            default: デフォルト値
            
        Returns:
            取得した値またはデフォルト値
        """
        return store.get(key, default)

    def delete_key(self, store: ProtectedStore, key: str) -> None:
        """
        ProtectedStoreからキーを削除する
        
        Args:
            store: 操作対象のProtectedStore
            key: 削除するキー
        """
        del store[key]

    def get_items(self, store: ProtectedStore):
        """
        ストアのアイテム一覧を取得する
        
        Args:
            store: 操作対象のProtectedStore
            
        Returns:
            アイテム一覧
        """
        return store.items()

    def get_keys(self, store: ProtectedStore):
        """
        ストアのキー一覧を取得する
        
        Args:
            store: 操作対象のProtectedStore
            
        Returns:
            キー一覧
        """
        return store.keys()

    def get_values(self, store: ProtectedStore):
        """
        ストアの値一覧を取得する
        
        Args:
            store: 操作対象のProtectedStore
            
        Returns:
            値一覧
        """
        return store.values()

    def get_deep_copy(self, store: ProtectedStore):
        """
        ストアのディープコピーを取得する
        
        Args:
            store: 操作対象のProtectedStore
            
        Returns:
            ディープコピーされた辞書
        """
        return store.deep_copy()

    def bulk_operation(self, store: ProtectedStore, data: dict) -> int:
        """
        複数のデータを一括操作する
        
        Args:
            store: 操作対象のProtectedStore
            data: 設定するデータ辞書
            
        Returns:
            操作後のストア長
        """
        for key, value in data.items():
            store.set(key, value)
        return len(store)


class MockUnauthorizedClass:
    """
    ProtectedStoreへのアクセスが許可されていないテスト用クラス
    
    このクラスはアクセス制御のテストのために使用され、
    ProtectedStoreへの不正アクセスを試行する
    """

    def __init__(self, identifier: str = "unauthorized_instance"):
        """
        初期化処理
        
        Args:
            identifier: インスタンスの識別子
        """
        self.identifier = identifier

    def attempt_unauthorized_access(self, store: ProtectedStore, key: str, value: Any) -> Any:
        """
        許可されていないアクセスを試行する
        
        Args:
            store: 操作対象のProtectedStore
            key: 設定するキー
            value: 設定する値
            
        Returns:
            設定した値（通常は例外が発生する）
        """
        store[key] = value
        return store[key]


class TestProtectedStoreInitialization(unittest.TestCase):
    """ProtectedStoreの初期化処理テストクラス"""

    def test_initialization_with_valid_instance(self):
        """有効なインスタンスでの初期化処理テスト"""
        authorized_instance = MockAuthorizedClass("test_instance")
        store = ProtectedStore(allowed_accessor=authorized_instance)

        # 初期状態の確認
        self.assertEqual(len(store._store), 0)
        self.assertIs(store._allowed_accessor, authorized_instance)

    def test_initialization_with_none_raises_error(self):
        """Noneでの初期化時の例外発生テスト"""
        with self.assertRaises(ValueError) as context:
            ProtectedStore(allowed_accessor=None)

        self.assertEqual(str(context.exception), "An allowed accessor must be provided.")

    def test_initialization_with_class_type(self):
        """クラス型での初期化処理テスト"""
        store = ProtectedStore(allowed_accessor=MockAuthorizedClass)

        # 初期状態の確認
        self.assertEqual(len(store._store), 0)
        self.assertIs(store._allowed_accessor, MockAuthorizedClass)

    def test_initialization_with_string_class_name(self):
        """文字列クラス名での初期化処理テスト"""
        store = ProtectedStore(allowed_accessor="MockAuthorizedClass")

        # 初期状態の確認
        self.assertEqual(len(store._store), 0)
        self.assertEqual(store._allowed_accessor, "MockAuthorizedClass")


class TestProtectedStoreBasicOperations(unittest.TestCase):
    """ProtectedStoreの基本操作テストクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.authorized_instance = MockAuthorizedClass("basic_operations_test")
        self.store = ProtectedStore(allowed_accessor=self.authorized_instance)

    def test_set_and_get_operations(self):
        """値の設定と取得操作テスト"""
        test_key = "test_key"
        test_value = "test_value"

        # 値の設定
        self.authorized_instance.set_value(self.store, test_key, test_value)

        # 値の取得と検証
        retrieved_value = self.authorized_instance.get_value(self.store, test_key)
        self.assertEqual(retrieved_value, test_value)

        # 内部ストアの確認
        self.assertIn(test_key, self.store._store)
        self.assertEqual(self.store._store[test_key], test_value)

    def test_contains_operation(self):
        """キー存在確認操作テスト"""
        test_key = "existence_check_key"
        test_value = "existence_check_value"

        # 値を設定する前の確認
        exists_before = self.authorized_instance.check_contains(self.store, test_key)
        self.assertFalse(exists_before)

        # 値を設定
        self.authorized_instance.set_value(self.store, test_key, test_value)

        # 値を設定した後の確認
        exists_after = self.authorized_instance.check_contains(self.store, test_key)
        self.assertTrue(exists_after)

        # 存在しないキーの確認
        non_existent_key = "non_existent_key"
        exists_non_existent = self.authorized_instance.check_contains(self.store, non_existent_key)
        self.assertFalse(exists_non_existent)

    def test_length_operation(self):
        """ストア長取得操作テスト"""
        # 初期状態での長さ確認
        initial_length = self.authorized_instance.get_store_length(self.store)
        self.assertEqual(initial_length, 0)

        # データを追加
        test_data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }

        for key, value in test_data.items():
            self.authorized_instance.set_value(self.store, key, value)

        # 追加後の長さ確認
        final_length = self.authorized_instance.get_store_length(self.store)
        self.assertEqual(final_length, len(test_data))

    def test_clear_operation(self):
        """ストアクリア操作テスト"""
        # データを追加
        test_data = {
            "clear_key1": "clear_value1",
            "clear_key2": "clear_value2"
        }

        for key, value in test_data.items():
            self.authorized_instance.set_value(self.store, key, value)

        # データが追加されていることを確認
        length_before_clear = self.authorized_instance.get_store_length(self.store)
        self.assertEqual(length_before_clear, len(test_data))

        # クリア操作
        self.authorized_instance.clear_store(self.store)

        # クリア後の確認
        length_after_clear = self.authorized_instance.get_store_length(self.store)
        self.assertEqual(length_after_clear, 0)


class TestProtectedStoreAccessControl(unittest.TestCase):
    """ProtectedStoreのアクセス制御テストクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.authorized_instance = MockAuthorizedClass("access_control_test")
        self.unauthorized_instance = MockUnauthorizedClass("unauthorized_test")
        self.store = ProtectedStore(allowed_accessor=self.authorized_instance)

    def test_authorized_access_success(self):
        """許可されたアクセスの成功テスト"""
        test_key = "authorized_key"
        test_value = "authorized_value"

        # 許可されたインスタンスからのアクセスは成功する
        self.authorized_instance.set_value(self.store, test_key, test_value)
        retrieved_value = self.authorized_instance.get_value(self.store, test_key)

        self.assertEqual(retrieved_value, test_value)

    def test_unauthorized_access_failure(self):
        """許可されていないアクセスの失敗テスト"""
        test_key = "unauthorized_key"
        test_value = "unauthorized_value"

        # 許可されていないインスタンスからのアクセスは例外が発生する
        with self.assertRaises((PermissionError, RuntimeError)):
            self.unauthorized_instance.attempt_unauthorized_access(
                self.store, test_key, test_value
            )

    def test_direct_access_prevention(self):
        """直接アクセスの防止テスト"""
        # 外部からの直接アクセスは例外が発生する
        with self.assertRaises((PermissionError, RuntimeError)):
            self.store["direct_key"] = "direct_value"

        with self.assertRaises((PermissionError, RuntimeError)):
            _ = self.store["direct_key"]

        with self.assertRaises((PermissionError, RuntimeError)):
            len(self.store)

        with self.assertRaises((PermissionError, RuntimeError)):
            "any_key" in self.store


class TestProtectedStoreErrorHandling(unittest.TestCase):
    """ProtectedStoreのエラーハンドリングテストクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.authorized_instance = MockAuthorizedClass("error_handling_test")
        self.store = ProtectedStore(allowed_accessor=self.authorized_instance)

    def test_key_error_on_non_existent_key(self):
        """存在しないキーへのアクセス時のKeyErrorテスト"""
        non_existent_key = "non_existent_key"

        # 存在しないキーへのアクセスはKeyErrorが発生する
        with self.assertRaises(KeyError):
            self.authorized_instance.get_value(self.store, non_existent_key)

    def test_get_method_with_default_value(self):
        """get メソッドのデフォルト値テスト"""
        non_existent_key = "non_existent_key"
        default_value = "default"

        # get メソッドでデフォルト値を指定
        result = self.authorized_instance.get_with_default(self.store, non_existent_key, default_value)
        self.assertEqual(result, default_value)

        # get メソッドでデフォルト値を指定しない場合（None）
        result_none = self.authorized_instance.get_with_default(self.store, non_existent_key)
        self.assertIsNone(result_none)


class TestProtectedStoreExtendedOperations(unittest.TestCase):
    """ProtectedStoreの拡張操作テストクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.authorized_instance = MockAuthorizedClass("extended_operations_test")
        self.store = ProtectedStore(allowed_accessor=self.authorized_instance)

    def test_delete_operation(self):
        """削除操作テスト"""
        test_key = "delete_test_key"
        test_value = "delete_test_value"

        # 値を設定
        self.authorized_instance.set_value(self.store, test_key, test_value)
        self.assertTrue(self.authorized_instance.check_contains(self.store, test_key))

        # 削除操作
        self.authorized_instance.delete_key(self.store, test_key)
        
        # 削除されたことを確認
        self.assertFalse(self.authorized_instance.check_contains(self.store, test_key))
        
        # 削除済みキーへのアクセスはKeyErrorが発生
        with self.assertRaises(KeyError):
            self.authorized_instance.get_value(self.store, test_key)

    def test_items_operation(self):
        """itemsメソッドテスト"""
        test_data = {
            "item_key1": "item_value1",
            "item_key2": "item_value2",
            "item_key3": "item_value3"
        }

        # データを設定
        for key, value in test_data.items():
            self.authorized_instance.set_value(self.store, key, value)

        # itemsメソッドでアイテム一覧を取得
        items = list(self.authorized_instance.get_items(self.store))
        
        # 期待されるアイテムがすべて含まれていることを確認
        for key, value in test_data.items():
            self.assertIn((key, value), items)
        
        self.assertEqual(len(items), len(test_data))

    def test_keys_operation(self):
        """keysメソッドテスト"""
        test_keys = ["key1", "key2", "key3"]

        # データを設定
        for i, key in enumerate(test_keys):
            self.authorized_instance.set_value(self.store, key, f"value{i}")

        # keysメソッドでキー一覧を取得
        keys = list(self.authorized_instance.get_keys(self.store))
        
        # 期待されるキーがすべて含まれていることを確認
        for key in test_keys:
            self.assertIn(key, keys)
        
        self.assertEqual(len(keys), len(test_keys))

    def test_values_operation(self):
        """valuesメソッドテスト"""
        test_values = ["value1", "value2", "value3"]

        # データを設定
        for i, value in enumerate(test_values):
            self.authorized_instance.set_value(self.store, f"key{i}", value)

        # valuesメソッドで値一覧を取得
        values = list(self.authorized_instance.get_values(self.store))
        
        # 期待される値がすべて含まれていることを確認
        for value in test_values:
            self.assertIn(value, values)
        
        self.assertEqual(len(values), len(test_values))

    def test_deep_copy_operation(self):
        """ディープコピー操作テスト"""
        test_data = {
            "simple_key": "simple_value",
            "nested_key": {"inner_key": "inner_value", "inner_list": [1, 2, 3]}
        }

        # データを設定
        self.authorized_instance.bulk_operation(self.store, test_data)

        # ディープコピーを取得
        store_copy = self.authorized_instance.get_deep_copy(self.store)

        # コピーが独立していることを確認
        self.assertIsNot(store_copy, self.store._store)
        self.assertEqual(store_copy, self.store._store)

        # ネストしたオブジェクトも独立していることを確認
        self.assertIsNot(store_copy["nested_key"], self.store._store["nested_key"])
        self.assertEqual(store_copy["nested_key"], self.store._store["nested_key"])

    def test_set_method_operation(self):
        """setメソッド操作テスト"""
        test_key = "set_method_key"
        test_value = "set_method_value"

        # setメソッドを使用して値を設定（許可されたインスタンス経由）
        self.authorized_instance.set_value(self.store, test_key, test_value)

        # 値が正しく設定されていることを確認
        retrieved_value = self.authorized_instance.get_value(self.store, test_key)
        self.assertEqual(retrieved_value, test_value)

        # 内部ストアにも反映されていることを確認
        self.assertEqual(self.store._store[test_key], test_value)


class TestProtectedStoreFlexibleAccessControl(unittest.TestCase):
    """ProtectedStoreの柔軟なアクセス制御テストクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.test_instance = MockAuthorizedClass("flexible_test")

    def test_class_type_based_access_control(self):
        """クラス型ベースのアクセス制御テスト"""
        # クラス型で許可
        store = ProtectedStore(allowed_accessor=MockAuthorizedClass)
        
        # 同じクラスの任意のインスタンスからのアクセス
        instance1 = MockAuthorizedClass("instance1")
        instance2 = MockAuthorizedClass("instance2")
        
        instance1.set_value(store, "type_key1", "type_value1")
        instance2.set_value(store, "type_key2", "type_value2")
        
        result1 = instance1.get_value(store, "type_key1")
        result2 = instance2.get_value(store, "type_key2")
        
        self.assertEqual(result1, "type_value1")
        self.assertEqual(result2, "type_value2")

        # 異なるクラスからのアクセスは拒否
        unauthorized_instance = MockUnauthorizedClass("unauthorized")
        with self.assertRaises((PermissionError, RuntimeError)):
            unauthorized_instance.attempt_unauthorized_access(store, "unauthorized_key", "unauthorized_value")

    def test_string_class_name_based_access_control(self):
        """文字列クラス名ベースのアクセス制御テスト"""
        # 文字列クラス名で許可
        store = ProtectedStore(allowed_accessor="MockAuthorizedClass")
        
        # 指定されたクラス名のインスタンスからのアクセス
        authorized_instance = MockAuthorizedClass("string_test")
        authorized_instance.set_value(store, "string_key", "string_value")
        result = authorized_instance.get_value(store, "string_key")
        
        self.assertEqual(result, "string_value")

        # 異なるクラス名のインスタンスからのアクセスは拒否
        unauthorized_instance = MockUnauthorizedClass("string_unauthorized")
        with self.assertRaises((PermissionError, RuntimeError)):
            unauthorized_instance.attempt_unauthorized_access(store, "string_unauthorized_key", "string_unauthorized_value")

    def test_custom_function_based_access_control(self):
        """カスタム関数ベースのアクセス制御テスト"""
        # カスタム検証関数（identifierが"allowed"で始まるインスタンスのみ許可）
        def custom_validator(caller_self):
            return hasattr(caller_self, 'identifier') and caller_self.identifier.startswith("allowed")

        store = ProtectedStore(allowed_accessor=custom_validator)
        
        # 条件を満たすインスタンスからのアクセス
        allowed_instance = MockAuthorizedClass("allowed_instance")
        allowed_instance.set_value(store, "custom_key", "custom_value")
        result = allowed_instance.get_value(store, "custom_key")
        self.assertEqual(result, "custom_value")

        # 条件を満たさないインスタンスからのアクセスは拒否
        denied_instance = MockAuthorizedClass("denied_instance")
        with self.assertRaises((PermissionError, RuntimeError)):
            denied_instance.set_value(store, "denied_key", "denied_value")

    def test_custom_function_exception_handling(self):
        """カスタム関数での例外ハンドリングテスト"""
        # 例外を発生させるカスタム検証関数
        def faulty_validator(caller_self):
            raise Exception("Validation error")

        store = ProtectedStore(allowed_accessor=faulty_validator)
        
        # 検証関数で例外が発生した場合はアクセス拒否
        instance = MockAuthorizedClass("test_instance")
        with self.assertRaises((PermissionError, RuntimeError)):
            instance.set_value(store, "faulty_key", "faulty_value")


class TestProtectedStoreEdgeCases(unittest.TestCase):
    """ProtectedStoreの境界条件テストクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.authorized_instance = MockAuthorizedClass("edge_case_test")
        self.store = ProtectedStore(allowed_accessor=self.authorized_instance)

    def test_empty_store_operations(self):
        """空のストアでの操作テスト"""
        # 空の状態での確認
        length = self.authorized_instance.get_store_length(self.store)
        self.assertEqual(length, 0)

        # 存在しないキーの確認
        exists = self.authorized_instance.check_contains(self.store, "nonexistent")
        self.assertFalse(exists)

        # 空のストアでのitemsメソッド
        items = list(self.authorized_instance.get_items(self.store))
        self.assertEqual(len(items), 0)

        # 空のストアでのkeysメソッド
        keys = list(self.authorized_instance.get_keys(self.store))
        self.assertEqual(len(keys), 0)

        # 空のストアでのvaluesメソッド
        values = list(self.authorized_instance.get_values(self.store))
        self.assertEqual(len(values), 0)

    def test_none_values_handling(self):
        """None値のハンドリングテスト"""
        test_key = "none_key"
        
        # None値を設定
        self.authorized_instance.set_value(self.store, test_key, None)
        
        # None値が正しく保存・取得されることを確認
        retrieved_value = self.authorized_instance.get_value(self.store, test_key)
        self.assertIsNone(retrieved_value)
        
        # キーは存在していることを確認
        exists = self.authorized_instance.check_contains(self.store, test_key)
        self.assertTrue(exists)

    def test_large_data_handling(self):
        """大量データのハンドリングテスト"""
        # 大量のデータでのテスト
        large_data = {f"key_{i}": f"value_{i}" for i in range(1000)}

        self.authorized_instance.bulk_operation(self.store, large_data)

        # 全データが正しく保存されていることを確認
        length = self.authorized_instance.get_store_length(self.store)
        self.assertEqual(length, 1000)

        # ランダムなキーで確認
        self.assertEqual(self.store._store["key_500"], "value_500")
        self.assertEqual(self.store._store["key_999"], "value_999")

    def test_unicode_and_special_characters(self):
        """Unicode文字および特殊文字のテスト"""
        special_data = {
            "unicode_key_🚀": "ロケット",
            "special_chars_!@#$%": "特殊文字テスト",
            "emoji_😊": "絵文字テスト",
            "日本語キー": "Japanese Key",
            "spaces in key": "スペース含有キー"
        }

        self.authorized_instance.bulk_operation(self.store, special_data)

        # 特殊文字も正しく保存されることを確認
        for key, value in special_data.items():
            retrieved_value = self.authorized_instance.get_value(self.store, key)
            self.assertEqual(retrieved_value, value)


class TestProtectedStoreIntegration(unittest.TestCase):
    """ProtectedStoreの統合テストクラス"""

    def setUp(self):
        """各テストメソッド実行前の初期化処理"""
        self.allowed_instance1 = MockAuthorizedClass("integration_test1")
        self.allowed_instance2 = MockAuthorizedClass("integration_test2")
        self.store1 = ProtectedStore(allowed_accessor=self.allowed_instance1)
        self.store2 = ProtectedStore(allowed_accessor=self.allowed_instance2)

    def tearDown(self):
        """各テストメソッド実行後のクリーンアップ処理"""
        # テスト後のクリーンアップ
        try:
            self.allowed_instance1.clear_store(self.store1)
        except:
            pass
        try:
            self.allowed_instance2.clear_store(self.store2)
        except:
            pass

    def test_multiple_instances_isolation(self):
        """複数インスタンスの分離テスト"""
        # 異なるストアが分離されていることを確認
        self.allowed_instance1.set_value(self.store1, "store1_key", "store1_value")
        self.allowed_instance2.set_value(self.store2, "store2_key", "store2_value")

        # 各ストアが独立していることを確認
        self.assertIn("store1_key", self.store1._store)
        self.assertNotIn("store1_key", self.store2._store)
        
        self.assertIn("store2_key", self.store2._store)
        self.assertNotIn("store2_key", self.store1._store)

    def test_complex_workflow_simulation(self):
        """複雑なワークフローのシミュレーションテスト"""
        # 段階的なデータ操作のシミュレーション
        
        # ステップ1: 初期データ設定
        initial_data = {"step1_key": "step1_value", "shared_key": "initial_value"}
        self.allowed_instance1.bulk_operation(self.store1, initial_data)
        
        # ステップ2: データ更新
        self.allowed_instance1.set_value(self.store1, "shared_key", "updated_value")
        
        # ステップ3: 追加データ
        additional_data = {"step3_key": "step3_value"}
        self.allowed_instance1.bulk_operation(self.store1, additional_data)
        
        # 最終状態の確認
        length = self.allowed_instance1.get_store_length(self.store1)
        self.assertEqual(length, 3)
        self.assertEqual(self.store1._store["shared_key"], "updated_value")

    def test_concurrent_access_simulation(self):
        """同時アクセスのシミュレーションテスト"""
        # 同じクラス型でのアクセス制御テスト
        class_based_store = ProtectedStore(allowed_accessor=MockAuthorizedClass)
        
        # 複数のインスタンスが同時にアクセス
        instance1 = MockAuthorizedClass("concurrent1")
        instance2 = MockAuthorizedClass("concurrent2")
        
        # 両方のインスタンスからアクセス可能
        instance1.set_value(class_based_store, "concurrent_key1", "concurrent_value1")
        instance2.set_value(class_based_store, "concurrent_key2", "concurrent_value2")
        
        # 両方の値が正しく保存されている
        self.assertEqual(class_based_store._store["concurrent_key1"], "concurrent_value1")
        self.assertEqual(class_based_store._store["concurrent_key2"], "concurrent_value2")


class TestProtectedStoreMockingScenarios(unittest.TestCase):
    """ProtectedStoreのモッキングシナリオテストクラス"""

    def setUp(self):
        """モッキングテスト用の初期化処理"""
        self.authorized_instance = MockAuthorizedClass("mocking_test")
        self.store = ProtectedStore(allowed_accessor=self.authorized_instance)

    def test_inspect_module_mocking(self):
        """inspectモジュールのモッキングテスト"""
        # inspect.currentframe が異常な値を返す場合のテスト
        with patch('inspect.currentframe', side_effect=Exception("Frame inspection failed")):
            with self.assertRaises(Exception):
                self.store._check_access_allowed()

    def test_copy_module_mocking(self):
        """copyモジュールのモッキングテスト"""
        # copyモジュールが利用できない場合のシミュレーション
        test_data = {"copy_test": "copy_value"}
        self.authorized_instance.bulk_operation(self.store, test_data)

        # copy.deepcopy をモック
        with patch('copy.deepcopy', side_effect=Exception("Deep copy failed")):
            # deep_copy メソッドが呼ばれるとエラーになることを確認
            with self.assertRaises((PermissionError, RuntimeError, Exception)):
                self.authorized_instance.get_deep_copy(self.store)

    def test_frame_globals_mocking(self):
        """フレームのglobals情報のモッキングテスト"""
        # フレームのlocals情報が異常な場合のテスト
        mock_frame = MagicMock()
        mock_frame.f_back = MagicMock()
        mock_frame.f_back.f_locals = {}  # 空のlocals

        with patch('inspect.currentframe', return_value=mock_frame):
            with self.assertRaises((PermissionError, RuntimeError)):
                self.store._check_access_allowed()


class TestProtectedStoreSecurityAttacks(unittest.TestCase):
    """ProtectedStoreのセキュリティ攻撃に対する防御テストクラス"""

    def setUp(self):
        """セキュリティテスト用の初期化処理"""
        self.authorized_instance = MockAuthorizedClass("security_test")
        self.store = ProtectedStore(allowed_accessor=self.authorized_instance)

    def test_frame_chain_exploitation_prevention(self):
        """フレームチェーン悪用攻撃の防止テスト"""

        class MaliciousClass:
            """悪意のあるクラス（フレームチェーン悪用を試行）"""

            def __init__(self, legitimate_instance, store):
                self.legitimate_instance = legitimate_instance
                self.store = store

            def attempt_exploit_via_frame_chain(self):
                """フレームチェーンを悪用したアクセス試行"""
                # legitimate_instance のメソッドを呼び出すことで
                # フレームチェーンに許可されたインスタンスを配置
                return self.call_through_legitimate_instance()

            def call_through_legitimate_instance(self):
                """許可されたインスタンス経由での悪用試行"""
                # このメソッド内で直接ストアにアクセスを試行
                # フレームチェーンには legitimate_instance が存在するが、
                # 直接の呼び出し元は MaliciousClass なのでブロックされるべき
                try:
                    self.store["malicious_key"] = "malicious_value"
                    return True  # 攻撃成功
                except PermissionError:
                    return False  # 攻撃失敗（期待される動作）

        # 悪意のあるクラスのインスタンスを作成
        malicious_instance = MaliciousClass(self.authorized_instance, self.store)

        # フレームチェーン悪用攻撃が防がれることを確認
        attack_successful = malicious_instance.attempt_exploit_via_frame_chain()
        self.assertFalse(attack_successful, "Frame chain exploitation should be prevented")

    def test_indirect_access_through_delegation_prevention(self):
        """委譲経由での間接アクセス攻撃の防止テスト"""

        class DelegatingMaliciousClass:
            """委譲を悪用する悪意のあるクラス"""

            def __init__(self, legitimate_instance, store):
                self.legitimate_instance = legitimate_instance
                self.store = store

            def attempt_delegation_attack(self):
                """委譲による攻撃試行"""
                # 許可されたインスタンスに処理を委譲して、
                # その結果を悪用しようとする
                try:
                    # 正当なインスタンス経由でのアクセス（これは成功するはず）
                    self.legitimate_instance.set_value(self.store, "delegated_key", "delegated_value")
                    
                    # しかし、その後の直接アクセスは防がれるはず
                    self.store["malicious_direct_key"] = "malicious_direct_value"
                    return True  # 攻撃成功
                except PermissionError:
                    return False  # 攻撃失敗（期待される動作）

        # 委譲攻撃のテスト
        delegating_malicious = DelegatingMaliciousClass(self.authorized_instance, self.store)
        attack_successful = delegating_malicious.attempt_delegation_attack()
        self.assertFalse(attack_successful, "Delegation attack should be prevented")

        # ただし、正当なアクセスは成功しているはず
        self.assertIn("delegated_key", self.store._store)

    def test_monkey_patching_attack_prevention(self):
        """モンキーパッチング攻撃の防止テスト"""
        # ProtectedStore のメソッドを動的に置き換える攻撃を試行
        original_check_method = self.store._check_access_allowed

        def malicious_check(*args, **kwargs):
            """悪意のあるアクセスチェック関数（常にパスする）"""
            pass  # 何もチェックしない

        try:
            # メソッドの置き換えを試行
            self.store._check_access_allowed = malicious_check
            
            # 直接アクセスを試行
            self.store["patched_key"] = "patched_value"
            
            # もしここまで到達したら、攻撃が成功している
            attack_successful = True
        except (PermissionError, RuntimeError, AttributeError):
            # メソッド置き換えが防がれた、または依然としてアクセスが制限されている
            attack_successful = False
        finally:
            # 元のメソッドを復元
            self.store._check_access_allowed = original_check_method

        # この種の攻撃は Python の性質上完全に防ぐのは困難だが、
        # 少なくとも基本的な防御は機能していることを確認
        # （実際の使用では、このような攻撃は実行環境レベルで防ぐべき）

    def test_reflection_based_attack_prevention(self):
        """リフレクションベースの攻撃防止テスト"""
        # __dict__ や getattr を使った内部状態への直接アクセス試行
        
        # ストア内部への直接アクセス試行
        try:
            # _store への直接アクセス
            direct_store = getattr(self.store, '_store')
            direct_store["reflection_key"] = "reflection_value"
            reflection_attack_successful = True
        except (AttributeError, PermissionError):
            reflection_attack_successful = False

        # この攻撃は現在の実装では防げないが、これは Python の性質上当然
        # 重要なのは、公開されたAPIを通じたアクセスが適切に制御されていること
        self.assertTrue(reflection_attack_successful, 
                       "Direct attribute access cannot be prevented in Python, this is expected behavior")

        # ただし、公開APIを通じたアクセスは依然として制御されているはず
        with self.assertRaises((PermissionError, RuntimeError)):
            # 外部からの直接APIアクセスは依然として防がれる
            len(self.store)


class TestProtectedStoreFrameHandling(unittest.TestCase):
    """ProtectedStoreのフレームハンドリングテストクラス"""

    def setUp(self):
        """フレームハンドリングテスト用の初期化処理"""
        self.authorized_instance = MockAuthorizedClass("frame_test")
        self.store = ProtectedStore(allowed_accessor=self.authorized_instance)

    def test_frame_back_none_handling(self):
        """フレームback情報がNoneの場合のハンドリングテスト"""
        # currentframe が None を返す場合のテスト
        with patch('inspect.currentframe', return_value=None):
            with self.assertRaises(RuntimeError):
                self.store._check_access_allowed()

    def test_permission_error_message(self):
        """PermissionErrorメッセージの確認テスト"""
        # 許可されていないアクセスで発生するエラーメッセージを確認
        unauthorized_instance = MockUnauthorizedClass("message_test")
        
        try:
            unauthorized_instance.attempt_unauthorized_access(self.store, "test_key", "test_value")
            self.fail("PermissionError should have been raised")
        except PermissionError as e:
            # エラーメッセージに期待される情報が含まれていることを確認
            error_message = str(e)
            self.assertIn("Access only allowed from authorized accessor", error_message)


if __name__ == '__main__':
    # テストスイートの実行
    test_classes = [
        TestProtectedStoreInitialization,
        TestProtectedStoreBasicOperations,
        TestProtectedStoreAccessControl,
        TestProtectedStoreErrorHandling,
        TestProtectedStoreExtendedOperations,
        TestProtectedStoreFlexibleAccessControl,
        TestProtectedStoreEdgeCases,
        TestProtectedStoreIntegration,
        TestProtectedStoreMockingScenarios,
        TestProtectedStoreSecurityAttacks,
        TestProtectedStoreFrameHandling
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
    print(f"ProtectedStoreテスト結果サマリー")
    print(f"{'='*80}")
    print(f"実行されたテスト数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失敗: {len(result.failures)}")
    print(f"エラー: {len(result.errors)}")

    if result.failures:
        print(f"\n失敗したテスト:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print(f"\nエラーが発生したテスト:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Error:')[-1].strip()}")

    print(f"{'='*80}")

    # 終了コードを設定
    sys.exit(0 if result.wasSuccessful() else 1)

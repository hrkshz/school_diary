"""インポートモデルのテスト"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from kits.io.models import DuplicateStrategy
from kits.io.models import ImportHistory
from kits.io.models import ImportMapping
from kits.io.models import ImportStatus

User = get_user_model()


class ImportMappingModelTestCase(TestCase):
    """ImportMappingモデルのテスト"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", name="テストユーザー", password="password123",
        )

    def test_create_mapping(self):
        """マッピングを作成できる"""
        mapping = ImportMapping.objects.create(
            code="test_mapping",
            name="テストマッピング",
            model_name="accounts.User",
            field_mapping={"名前": "name", "メール": "email"},
            unique_fields=["email"],
            duplicate_strategy=DuplicateStrategy.SKIP,
            created_by=self.user,
        )

        self.assertEqual(mapping.code, "test_mapping")
        self.assertEqual(mapping.name, "テストマッピング")
        self.assertTrue(mapping.is_active)

    def test_mapping_str(self):
        """__str__メソッドが正しく動作する"""
        mapping = ImportMapping.objects.create(
            code="test_mapping",
            name="テストマッピング",
            model_name="accounts.User",
            created_by=self.user,
        )

        self.assertEqual(str(mapping), "test_mapping - テストマッピング")


class ImportHistoryModelTestCase(TestCase):
    """ImportHistoryモデルのテスト"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", name="テストユーザー", password="password123",
        )

    def test_create_history(self):
        """インポート履歴を作成できる"""
        history = ImportHistory.objects.create(
            model_name="accounts.User",
            original_filename="test.csv",
            file_size=1024,
            encoding="utf-8",
            imported_by=self.user,
        )

        self.assertEqual(history.status, ImportStatus.PENDING)
        self.assertEqual(history.total_rows, 0)
        self.assertEqual(history.success_count, 0)

    def test_mark_as_processing(self):
        """処理中にマークできる"""
        history = ImportHistory.objects.create(
            model_name="accounts.User",
            original_filename="test.csv",
            imported_by=self.user,
        )

        history.mark_as_processing()

        self.assertEqual(history.status, ImportStatus.PROCESSING)
        self.assertIsNotNone(history.started_at)

    def test_mark_as_completed(self):
        """完了にマークできる"""
        history = ImportHistory.objects.create(
            model_name="accounts.User",
            original_filename="test.csv",
            imported_by=self.user,
            total_rows=100,
        )

        history.mark_as_completed(success_count=95, failed_count=5)

        self.assertEqual(history.status, ImportStatus.PARTIAL)
        self.assertEqual(history.success_count, 95)
        self.assertEqual(history.failed_count, 5)
        self.assertIsNotNone(history.completed_at)

    def test_mark_as_completed_all_success(self):
        """全て成功した場合のマーク"""
        history = ImportHistory.objects.create(
            model_name="accounts.User",
            original_filename="test.csv",
            imported_by=self.user,
            total_rows=100,
        )

        history.mark_as_completed(success_count=100, failed_count=0)

        self.assertEqual(history.status, ImportStatus.COMPLETED)

    def test_mark_as_failed(self):
        """失敗にマークできる"""
        history = ImportHistory.objects.create(
            model_name="accounts.User",
            original_filename="test.csv",
            imported_by=self.user,
        )

        history.mark_as_failed("エラーが発生しました")

        self.assertEqual(history.status, ImportStatus.FAILED)
        self.assertEqual(history.error_message, "エラーが発生しました")

    def test_success_rate(self):
        """成功率を計算できる"""
        history = ImportHistory.objects.create(
            model_name="accounts.User",
            original_filename="test.csv",
            imported_by=self.user,
            total_rows=100,
            success_count=80,
        )

        self.assertEqual(history.success_rate, 80.0)

    def test_success_rate_zero_rows(self):
        """総行数が0の場合の成功率"""
        history = ImportHistory.objects.create(
            model_name="accounts.User",
            original_filename="test.csv",
            imported_by=self.user,
            total_rows=0,
        )

        self.assertEqual(history.success_rate, 0.0)

    def test_add_error(self):
        """エラーを追加できる"""
        history = ImportHistory.objects.create(
            model_name="accounts.User",
            original_filename="test.csv",
            imported_by=self.user,
        )

        history.add_error(5, "email", "無効なメールアドレス")

        self.assertEqual(len(history.error_details), 1)
        self.assertEqual(history.error_details[0]["row"], 5)
        self.assertEqual(history.error_details[0]["field"], "email")

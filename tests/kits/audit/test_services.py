"""
Tests for kits.audit services.
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from kits.audit.models import AuditLog
from kits.audit.services import AuditService

User = get_user_model()


class MockModel:
    """テスト用のモックモデル。"""

    pk = 123

    class _meta:
        model_name = "mock_model"

    def __str__(self):
        return "Mock Object"


class AuditServiceTest(TestCase):
    """AuditServiceのテスト。"""

    def setUp(self):
        """テストデータのセットアップ。"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        self.service = AuditService()
        self.mock_obj = MockModel()

    def test_log_event(self):
        """イベントログ記録のテスト。"""
        log = self.service.log_event(
            event_type="create",
            event_name="オブジェクト作成",
            obj=self.mock_obj,
            user=self.user,
            description="新しいオブジェクトが作成されました",
        )

        self.assertIsInstance(log, AuditLog)
        self.assertEqual(log.event_type, "create")
        self.assertEqual(log.event_name, "オブジェクト作成")
        self.assertEqual(log.model_name, "mock_model")
        self.assertEqual(log.object_id, "123")
        self.assertEqual(log.user, self.user)

    def test_log_event_with_changes(self):
        """変更内容を含むイベントログのテスト。"""
        changes = {
            "status": {"from": "draft", "to": "published"},
        }

        log = self.service.log_event(
            event_type="update",
            event_name="ステータス変更",
            obj=self.mock_obj,
            user=self.user,
            changes=changes,
        )

        self.assertEqual(log.changes, changes)

    def test_log_event_with_metadata(self):
        """メタデータを含むイベントログのテスト。"""
        metadata = {
            "priority": "high",
            "department": "営業部",
        }

        log = self.service.log_event(
            event_type="approve",
            event_name="承認",
            obj=self.mock_obj,
            user=self.user,
            metadata=metadata,
        )

        self.assertEqual(log.metadata, metadata)

    def test_get_object_audit_logs(self):
        """オブジェクトの監査ログ取得のテスト。"""
        # ログを3つ作成
        for i in range(3):
            self.service.log_event(
                event_type="update",
                event_name=f"更新{i+1}",
                obj=self.mock_obj,
                user=self.user,
            )

        logs = self.service.get_object_audit_logs(self.mock_obj)
        self.assertEqual(len(logs), 3)

        # limitパラメータのテスト
        limited_logs = self.service.get_object_audit_logs(self.mock_obj, limit=2)
        self.assertEqual(len(limited_logs), 2)

    def test_search_logs_by_user(self):
        """ユーザーでフィルタした検索のテスト。"""
        # 別のユーザーを作成
        other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
        )

        # 各ユーザーでログを作成
        self.service.log_event(
            event_type="create",
            event_name="User1のイベント",
            obj=self.mock_obj,
            user=self.user,
        )

        self.service.log_event(
            event_type="create",
            event_name="User2のイベント",
            obj=self.mock_obj,
            user=other_user,
        )

        # ユーザーでフィルタ
        logs = self.service.search_logs(user=self.user)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].user, self.user)

    def test_search_logs_by_event_type(self):
        """イベントタイプでフィルタした検索のテスト。"""
        self.service.log_event(
            event_type="create",
            event_name="作成イベント",
            obj=self.mock_obj,
            user=self.user,
        )

        self.service.log_event(
            event_type="update",
            event_name="更新イベント",
            obj=self.mock_obj,
            user=self.user,
        )

        # createイベントのみ取得
        logs = self.service.search_logs(event_type="create")
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].event_type, "create")

    def test_search_logs_by_date_range(self):
        """日付範囲でフィルタした検索のテスト。"""
        now = timezone.now()
        yesterday = now - timedelta(days=1)

        # ログを作成（日付を手動で設定）
        log = AuditLog.objects.create(
            event_type="create",
            event_name="過去のイベント",
            model_name="test",
            object_id="1",
            object_repr="Test",
            user=self.user,
        )
        log.created_at = yesterday
        log.save()

        # 今日のログを作成
        self.service.log_event(
            event_type="create",
            event_name="今日のイベント",
            obj=self.mock_obj,
            user=self.user,
        )

        # 今日以降のログを検索
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        logs = self.service.search_logs(start_date=start_of_today)
        self.assertEqual(len(logs), 1)

    def test_get_user_activity(self):
        """ユーザーアクティビティ取得のテスト。"""
        # 複数のログを作成
        for i in range(5):
            self.service.log_event(
                event_type="update",
                event_name=f"アクティビティ{i+1}",
                obj=self.mock_obj,
                user=self.user,
            )

        activity = self.service.get_user_activity(self.user, days=30)
        self.assertEqual(len(activity), 5)

    def test_generate_audit_report(self):
        """監査レポート生成のテスト。"""
        # テストデータを作成
        for event_type in ["create", "update", "approve"]:
            self.service.log_event(
                event_type=event_type,
                event_name=f"{event_type}イベント",
                obj=self.mock_obj,
                user=self.user,
            )

        # レポート生成
        report = self.service.generate_audit_report()

        self.assertIn("total_events", report)
        self.assertEqual(report["total_events"], 3)

        self.assertIn("event_type_counts", report)
        self.assertEqual(report["event_type_counts"]["create"], 1)
        self.assertEqual(report["event_type_counts"]["update"], 1)
        self.assertEqual(report["event_type_counts"]["approve"], 1)

        self.assertIn("user_activity", report)
        self.assertIn("model_changes", report)

    def test_generate_audit_report_with_date_range(self):
        """日付範囲指定の監査レポート生成テスト。"""
        start_date = timezone.now() - timedelta(days=7)

        # ログを作成
        self.service.log_event(
            event_type="create",
            event_name="テストイベント",
            obj=self.mock_obj,
            user=self.user,
        )

        # ログ作成後に end_date を設定
        end_date = timezone.now()

        report = self.service.generate_audit_report(
            start_date=start_date,
            end_date=end_date,
        )

        self.assertEqual(report["start_date"], start_date)
        self.assertEqual(report["end_date"], end_date)
        self.assertGreater(report["total_events"], 0)

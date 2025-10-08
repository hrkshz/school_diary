"""
Tests for kits.audit models.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from kits.audit.models import AuditLog

User = get_user_model()


class AuditLogModelTest(TestCase):
    """AuditLogモデルのテスト。"""

    def setUp(self):
        """テストデータのセットアップ。"""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )

    def test_create_audit_log(self):
        """監査ログの作成テスト。"""
        log = AuditLog.objects.create(
            event_type="create",
            event_name="テストイベント",
            model_name="test_model",
            object_id="123",
            object_repr="Test Object",
            user=self.user,
        )

        self.assertEqual(log.event_type, "create")
        self.assertEqual(log.event_name, "テストイベント")
        self.assertEqual(log.user, self.user)

    def test_audit_log_str(self):
        """監査ログの文字列表現テスト。"""
        log = AuditLog.objects.create(
            event_type="update",
            event_name="更新イベント",
            model_name="test_model",
            object_id="456",
            object_repr="Test Object 2",
        )

        expected = f"更新イベント - Test Object 2 ({log.created_at})"
        self.assertEqual(str(log), expected)

    def test_audit_log_with_changes(self):
        """変更内容を含む監査ログのテスト。"""
        changes = {
            "status": {"old": "draft", "new": "published"},
            "title": {"old": "Old Title", "new": "New Title"},
        }

        log = AuditLog.objects.create(
            event_type="update",
            event_name="ドキュメント更新",
            model_name="document",
            object_id="789",
            object_repr="Document ABC",
            changes=changes,
            user=self.user,
        )

        self.assertEqual(log.changes, changes)
        self.assertIn("status", log.changes)
        self.assertEqual(log.changes["status"]["old"], "draft")
        self.assertEqual(log.changes["status"]["new"], "published")

    def test_audit_log_with_metadata(self):
        """メタデータを含む監査ログのテスト。"""
        metadata = {
            "department": "営業部",
            "priority": "high",
            "ip_address": "192.168.1.100",
        }

        log = AuditLog.objects.create(
            event_type="approve",
            event_name="承認イベント",
            model_name="approval",
            object_id="101",
            object_repr="Approval Request",
            metadata=metadata,
            user=self.user,
        )

        self.assertEqual(log.metadata, metadata)
        self.assertEqual(log.metadata["department"], "営業部")
        self.assertEqual(log.metadata["priority"], "high")

    def test_audit_log_ordering(self):
        """監査ログの並び順テスト（新しい順）。"""
        log1 = AuditLog.objects.create(
            event_type="create",
            event_name="イベント1",
            model_name="test",
            object_id="1",
            object_repr="Obj 1",
        )

        log2 = AuditLog.objects.create(
            event_type="update",
            event_name="イベント2",
            model_name="test",
            object_id="2",
            object_repr="Obj 2",
        )

        logs = AuditLog.objects.all()
        self.assertEqual(logs[0].id, log2.id)  # 新しい順
        self.assertEqual(logs[1].id, log1.id)

    def test_audit_log_event_type_choices(self):
        """イベントタイプの選択肢テスト。"""
        expected_types = [
            "create",
            "update",
            "delete",
            "approve",
            "reject",
            "submit",
            "cancel",
            "custom",
        ]

        for event_type, _ in AuditLog.EVENT_TYPE_CHOICES:
            self.assertIn(event_type, expected_types)

        self.assertEqual(len(AuditLog.EVENT_TYPE_CHOICES), 8)

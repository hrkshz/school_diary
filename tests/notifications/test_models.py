"""
モデルのテスト
"""

from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.test import TestCase

from kits.notifications.models import Notification
from kits.notifications.models import NotificationStatus
from kits.notifications.models import NotificationTemplate
from kits.notifications.models import NotificationType

if TYPE_CHECKING:
    from school_diary.users.models import User
else:
    User = get_user_model()


class NotificationTemplateTestCase(TestCase):
    """NotificationTemplateモデルのテスト"""

    def setUp(self):
        self.template = NotificationTemplate.objects.create(
            code="test_template",
            name="テストテンプレート",
            subject_template="{{ user.name }}様へのお知らせ",
            body_template="こんにちは、{{ user.name }}さん！",
            notification_types=[NotificationType.EMAIL],
        )

    def test_template_creation(self):
        """テンプレートが正しく作成できる"""
        self.assertEqual(self.template.code, "test_template")
        self.assertTrue(self.template.is_active)

    def test_template_str(self):
        """__str__メソッドが正しく動作する"""
        expected = "test_template - テストテンプレート"
        self.assertEqual(str(self.template), expected)


class NotificationTestCase(TestCase):
    """Notificationモデルのテスト"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="password123",
        )
        self.user.first_name = "テストユーザー"
        self.user.save()

        self.notification = Notification.objects.create(
            recipient=self.user,
            recipient_email=self.user.email,
            notification_type=NotificationType.EMAIL,
            subject="テスト通知",
            body="これはテストです",
        )

    def test_notification_creation(self):
        """通知が正しく作成できる"""
        self.assertEqual(self.notification.recipient, self.user)
        self.assertEqual(self.notification.status, NotificationStatus.PENDING)

    def test_mark_as_sent(self):
        """送信完了マークが正しく動作する"""
        self.notification.mark_as_sent()
        self.assertEqual(self.notification.status, NotificationStatus.SENT)
        self.assertIsNotNone(self.notification.sent_at)

    def test_mark_as_read(self):
        """既読マークが正しく動作する"""
        self.notification.mark_as_sent()
        self.notification.mark_as_read()
        self.assertEqual(self.notification.status, NotificationStatus.READ)
        self.assertIsNotNone(self.notification.read_at)

    def test_mark_as_failed(self):
        """失敗マークが正しく動作する"""
        error_msg = "Test error"
        self.notification.mark_as_failed(error_msg)
        self.assertEqual(self.notification.status, NotificationStatus.FAILED)
        self.assertEqual(self.notification.error_message, error_msg)
        self.assertEqual(self.notification.retry_count, 1)

    def test_can_retry(self):
        """リトライ可否が正しく判定される"""
        # 初回失敗
        self.notification.mark_as_failed("Error")
        self.assertTrue(self.notification.can_retry)

        # 3回失敗(上限)
        self.notification.retry_count = 3
        self.notification.save()
        self.assertFalse(self.notification.can_retry)

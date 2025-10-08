"""
サービス層のテスト
"""
from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model
from django.test import TestCase

from kits.notifications.models import NotificationTemplate
from kits.notifications.models import NotificationType
from kits.notifications.services import NotificationService
from kits.notifications.services import NotificationTemplateRenderer

if TYPE_CHECKING:
    from school_diary.users.models import User
else:
    User = get_user_model()


class NotificationTemplateRendererTestCase(TestCase):
    """NotificationTemplateRendererのテスト"""

    def test_render_subject(self):
        """件名レンダリングが正しく動作する"""
        template = '{{ user.name }}様へのお知らせ'
        context = {'user': type('User', (), {'name': 'テスト太郎'})}

        result = NotificationTemplateRenderer.render_subject(template, context)
        self.assertEqual(result, 'テスト太郎様へのお知らせ')

    def test_render_body_with_markdown(self):
        """Markdown変換が正しく動作する"""
        template = '# 見出し\n\n**太字**のテキスト'
        result = NotificationTemplateRenderer.render_body(template, {})

        self.assertIn('<h1>見出し</h1>', result)
        self.assertIn('<strong>太字</strong>', result)


class NotificationServiceTestCase(TestCase):
    """NotificationServiceのテスト"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='テストユーザー',
            password='password123'
        )

        self.template = NotificationTemplate.objects.create(
            code='test_notification',
            name='テスト通知',
            subject_template='{{ user.name }}様、{{ message }}',
            body_template='こんにちは、{{ user.name }}さん！\n\n{{ content }}',
            notification_types=[NotificationType.EMAIL],
        )

        self.service = NotificationService()

    def test_create_from_template(self):
        """テンプレートから通知が作成できる"""
        context = {
            'message': 'お知らせがあります',
            'content': 'テスト内容です',
        }

        notification = self.service.create_from_template(
            template_code='test_notification',
            recipient=self.user,
            context=context,
        )

        self.assertEqual(notification.recipient, self.user)
        self.assertIn('テストユーザー', notification.subject)
        self.assertIn('お知らせがあります', notification.subject)
        self.assertIn('テスト内容です', notification.body)

    def test_get_unread_count(self):
        """未読通知数が正しく取得できる"""
        # IN_APP通知を3件作成
        for i in range(3):
            notification = self.service.create_from_template(
                template_code='test_notification',
                recipient=self.user,
                context={'message': f'通知{i}', 'content': 'テスト'},
                notification_type=NotificationType.IN_APP,
            )
            # 送信済みステータスにする
            notification.mark_as_sent()

        count = self.service.get_unread_count(self.user)
        self.assertEqual(count, 3)

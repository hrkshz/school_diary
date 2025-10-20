"""
通知サービス層

通知の作成、送信、テンプレートレンダリングを担当します。
"""

import logging
from typing import TYPE_CHECKING
from typing import Any

import bleach
import markdown
from django.conf import settings
from django.contrib.auth import get_user_model
from django.template import Context
from django.template import Template
from django.utils import timezone

from .models import Notification
from .models import NotificationStatus
from .models import NotificationTemplate
from .models import NotificationType

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser as User
else:
    User = get_user_model()

logger = logging.getLogger(__name__)


class NotificationTemplateRenderer:
    """
    通知テンプレートのレンダリングを担当

    Django Template言語を使ってテンプレートをレンダリングし、
    Markdownの変換、HTMLのサニタイズを行います。
    """

    ALLOWED_TAGS = [
        "a",
        "abbr",
        "acronym",
        "b",
        "blockquote",
        "code",
        "em",
        "i",
        "li",
        "ol",
        "p",
        "strong",
        "ul",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "br",
        "div",
        "span",
    ]

    ALLOWED_ATTRIBUTES = {
        "a": ["href", "title"],
        "abbr": ["title"],
        "acronym": ["title"],
    }

    @classmethod
    def render_subject(cls, template_str: str, context: dict[str, Any]) -> str:
        """
        件名をレンダリング

        Args:
            template_str: テンプレート文字列
            context: コンテキストデータ

        Returns:
            レンダリング済みの件名
        """
        template = Template(template_str)
        rendered = template.render(Context(context))
        # 件名は1行のみ、余分な空白を削除
        return rendered.strip().replace("\n", " ")

    @classmethod
    def render_body(cls, template_str: str, context: dict[str, Any], use_markdown: bool = True) -> str:
        """
        本文をレンダリング

        Args:
            template_str: テンプレート文字列
            context: コンテキストデータ
            use_markdown: Markdownを使用するか

        Returns:
            レンダリング済みの本文
        """
        template = Template(template_str)
        rendered = template.render(Context(context))

        if use_markdown:
            # MarkdownをHTMLに変換
            html = markdown.markdown(
                rendered,
                extensions=["extra", "nl2br", "sane_lists"],
            )
            # HTMLをサニタイズ(XSS対策)
            return bleach.clean(
                html,
                tags=cls.ALLOWED_TAGS,
                attributes=cls.ALLOWED_ATTRIBUTES,
                strip=True,
            )

        return rendered


class NotificationService:
    """
    通知サービス

    通知の作成、送信、履歴管理を行います。
    """

    def __init__(self):
        self.config = getattr(settings, "NOTIFICATIONS_CONFIG", {})
        self.enabled = self.config.get("ENABLED", True)

    def create_from_template(
        self,
        template_code: str,
        recipient: User,
        context: dict[str, Any],
        notification_type: str = NotificationType.EMAIL,
        priority: str = "normal",
        scheduled_at: timezone.datetime | None = None,
        related_object_type: str = "",
        related_object_id: str = "",
    ) -> Notification:
        """
        テンプレートから通知を作成

        Args:
            template_code: テンプレートコード
            recipient: 受信者
            context: テンプレートに渡すコンテキスト
            notification_type: 通知タイプ
            priority: 優先度
            scheduled_at: 送信予定日時
            related_object_type: 関連オブジェクトタイプ
            related_object_id: 関連オブジェクトID

        Returns:
            作成された通知オブジェクト

        Raises:
            NotificationTemplate.DoesNotExist: テンプレートが見つからない
        """
        # テンプレートを取得
        template = NotificationTemplate.objects.get(
            code=template_code,
            is_active=True,
        )

        # ユーザー情報をコンテキストに追加
        context.setdefault("user", recipient)
        context.setdefault("site_name", "school_diary")

        # テンプレートをレンダリング
        subject = NotificationTemplateRenderer.render_subject(
            template.subject_template,
            context,
        )
        body = NotificationTemplateRenderer.render_body(
            template.body_template,
            context,
            use_markdown=True,
        )

        # HTML本文(オプショナル)
        html_body = ""
        if template.html_template:
            html_body = NotificationTemplateRenderer.render_body(
                template.html_template,
                context,
                use_markdown=False,
            )

        # JSONシリアライズ可能なcontext_dataを作成
        # Djangoモデルインスタンスなどのオブジェクトを除外
        serializable_context = {}
        for key, value in context.items():
            # Djangoモデルインスタンス(_metaを持つオブジェクト)をスキップ
            if not hasattr(value, "_meta"):
                serializable_context[key] = value

        # 通知オブジェクトを作成
        notification = Notification.objects.create(
            recipient=recipient,
            recipient_email=recipient.email,
            template=template,
            notification_type=notification_type,
            priority=priority,
            subject=subject,
            body=body,
            html_body=html_body,
            context_data=serializable_context,
            scheduled_at=scheduled_at,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
        )

        logger.info(
            f"通知作成: {notification.pk} - {template_code} → {recipient.email}",
        )

        return notification

    def send_notification(self, notification: Notification) -> bool:
        """
        通知を送信

        Args:
            notification: 送信する通知オブジェクト

        Returns:
            送信成功したかどうか
        """
        if not self.enabled:
            logger.warning("通知機能が無効化されています")
            return False

        # スケジュール確認
        if notification.scheduled_at and notification.scheduled_at > timezone.now():
            logger.info(f"通知 {notification.pk} は {notification.scheduled_at} に送信予定")
            return False

        try:
            notification.status = NotificationStatus.SENDING
            notification.save(update_fields=["status"])

            # 通知タイプに応じて送信
            if notification.notification_type == NotificationType.EMAIL:
                self._send_email(notification)
            elif notification.notification_type == NotificationType.IN_APP:
                self._send_in_app(notification)
            else:
                msg = f"未実装の通知タイプ: {notification.notification_type}"
                raise NotImplementedError(
                    msg,
                )

            # 送信完了
            notification.mark_as_sent()
            logger.info(f"通知送信成功: {notification.pk}")
            return True

        except Exception as e:
            # エラーハンドリング
            error_message = str(e)
            notification.mark_as_failed(error_message)
            logger.exception(f"通知送信失敗: {notification.pk} - {error_message}")
            return False

    def _send_email(self, notification: Notification):
        """メール送信"""
        from django.core.mail import EmailMultiAlternatives

        email = EmailMultiAlternatives(
            subject=notification.subject,
            body=notification.body,  # プレーンテキスト版
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[notification.recipient_email],
        )

        # HTML版があれば添付
        if notification.html_body:
            email.attach_alternative(notification.html_body, "text/html")

        email.send()

    def _send_in_app(self, notification: Notification):
        """アプリ内通知(データベースに保存するだけ)"""
        # すでにNotificationモデルに保存されているので、
        # ステータスを更新するだけ

    def send_batch(self, notifications: list[Notification]) -> dict[str, int]:
        """
        通知を一括送信

        Args:
            notifications: 送信する通知のリスト

        Returns:
            送信結果の統計(成功数、失敗数)
        """
        batch_size = self.config.get("BATCH_SIZE", 100)
        success_count = 0
        failed_count = 0

        for notification in notifications[:batch_size]:
            if self.send_notification(notification):
                success_count += 1
            else:
                failed_count += 1

        return {
            "success": success_count,
            "failed": failed_count,
            "total": success_count + failed_count,
        }

    def get_unread_count(self, user: User) -> int:
        """未読通知数を取得"""
        return Notification.objects.filter(
            recipient=user,
            notification_type=NotificationType.IN_APP,
            status=NotificationStatus.SENT,
        ).count()

    def mark_all_as_read(self, user: User) -> int:
        """全ての通知を既読にする"""
        return Notification.objects.filter(
            recipient=user,
            notification_type=NotificationType.IN_APP,
            status=NotificationStatus.SENT,
        ).update(
            status=NotificationStatus.READ,
            read_at=timezone.now(),
        )

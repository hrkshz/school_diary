"""
通知システムのデータモデル

このモジュールは、通知の保存、テンプレート管理、
送信履歴の記録を担当します。
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class NotificationPriority(models.TextChoices):
    """通知の優先度"""

    LOW = "low", _("低")
    NORMAL = "normal", _("通常")
    HIGH = "high", _("高")
    URGENT = "urgent", _("緊急")


class NotificationStatus(models.TextChoices):
    """通知の送信状態"""

    PENDING = "pending", _("送信待ち")
    SENDING = "sending", _("送信中")
    SENT = "sent", _("送信完了")
    FAILED = "failed", _("送信失敗")
    READ = "read", _("既読")


class NotificationType(models.TextChoices):
    """通知の種類"""

    EMAIL = "email", _("メール")
    IN_APP = "in_app", _("アプリ内通知")
    PUSH = "push", _("プッシュ通知")
    SMS = "sms", _("SMS")


class NotificationTemplate(models.Model):
    """
    通知テンプレート

    再利用可能な通知テンプレートを管理します。
    Django Template言語を使用してパーソナライズされた通知を作成できます。
    """

    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("テンプレートコード"),
        help_text=_("システム内で使用する一意の識別子(例: approval_request)"),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("テンプレート名"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("説明"),
    )

    # テンプレート内容
    subject_template = models.CharField(
        max_length=255,
        verbose_name=_("件名テンプレート"),
        help_text=_("Django Template構文が使えます: {{ user.name }}様"),
    )
    body_template = models.TextField(
        verbose_name=_("本文テンプレート"),
        help_text=_("プレーンテキストまたはMarkdown形式"),
    )
    html_template = models.TextField(
        blank=True,
        verbose_name=_("HTMLテンプレート"),
        help_text=_("HTMLメール用(オプショナル)"),
    )

    # 設定
    notification_types = ArrayField(
        models.CharField(max_length=20, choices=NotificationType.choices),
        default=list,
        verbose_name=_("通知タイプ"),
        help_text=_("このテンプレートが対応する通知タイプ"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("有効"),
    )

    # メタ情報
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "kits_notification_templates"
        verbose_name = _("通知テンプレート")
        verbose_name_plural = _("通知テンプレート")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Notification(models.Model):
    """
    通知レコード

    個々の通知を表します。送信履歴、既読状態、
    エラー情報などを記録します。
    """

    # 受信者情報
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("受信者"),
    )
    recipient_email = models.EmailField(
        blank=True,
        verbose_name=_("受信者メールアドレス"),
        help_text=_("Userモデルのemailと異なる場合に使用"),
    )

    # テンプレート
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name=_("テンプレート"),
    )

    # 通知内容
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.EMAIL,
        verbose_name=_("通知タイプ"),
    )
    priority = models.CharField(
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        verbose_name=_("優先度"),
    )
    subject = models.CharField(
        max_length=255,
        verbose_name=_("件名"),
    )
    body = models.TextField(
        verbose_name=_("本文"),
    )
    html_body = models.TextField(
        blank=True,
        verbose_name=_("HTML本文"),
    )

    # コンテキストデータ: テンプレートレンダリング用
    context_data = models.JSONField(
        default=dict,
        verbose_name=_("コンテキストデータ"),
        help_text=_("テンプレートに渡されたデータ"),
    )

    # 状態管理
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
        verbose_name=_("ステータス"),
    )

    # タイムスタンプ
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("送信予定日時"),
        help_text=_("指定した場合、この日時に送信されます"),
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("送信日時"),
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("既読日時"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # エラー情報
    error_message = models.TextField(
        blank=True,
        verbose_name=_("エラーメッセージ"),
    )
    retry_count = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_("リトライ回数"),
    )

    # 関連オブジェクト(ジェネリックリレーション)
    # 例: 承認申請、健診予約など
    related_object_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("関連オブジェクトタイプ"),
    )
    related_object_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("関連オブジェクトID"),
    )

    class Meta:
        db_table = "kits_notifications"
        verbose_name = _("通知")
        verbose_name_plural = _("通知")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "status"]),
            models.Index(fields=["status", "scheduled_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        # Get display name for notification type
        if self.notification_type == "email":
            display_name = _("メール")
        elif self.notification_type == "in_app":
            display_name = _("アプリ内通知")
        elif self.notification_type == "push":
            display_name = _("プッシュ通知")
        elif self.notification_type == "sms":
            display_name = _("SMS")
        else:
            display_name = self.notification_type
        return f"{display_name}: {self.subject} → {self.recipient}"

    def mark_as_sent(self):
        """送信完了としてマーク"""
        self.status = NotificationStatus.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "sent_at", "updated_at"])

    def mark_as_read(self):
        """既読としてマーク"""
        if self.status == NotificationStatus.SENT:
            self.status = NotificationStatus.READ
            self.read_at = timezone.now()
            self.save(update_fields=["status", "read_at", "updated_at"])

    def mark_as_failed(self, error_message: str):
        """送信失敗としてマーク"""
        self.status = NotificationStatus.FAILED
        self.error_message = error_message
        self.retry_count += 1
        self.save(
            update_fields=[
                "status",
                "error_message",
                "retry_count",
                "updated_at",
            ],
        )

    @property
    def is_read(self) -> bool:
        """既読かどうか"""
        return self.status == NotificationStatus.READ

    @property
    def can_retry(self) -> bool:
        """リトライ可能かどうか"""
        max_retries = settings.NOTIFICATIONS_CONFIG.get("RETRY_ATTEMPTS", 3)
        return (
            self.status == NotificationStatus.FAILED and self.retry_count < max_retries
        )

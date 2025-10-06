"""
変更履歴追跡のためのモデルとヘルパー。

このモジュールはdjango-simple-historyをラップし、以下の機能を提供します:
- 自動的な変更履歴記録
- 変更理由の記録
- 変更ユーザーの記録
- 履歴の検索とフィルタリング
"""

from typing import TYPE_CHECKING

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

    User = AbstractUser
else:
    from django.contrib.auth import get_user_model

    User = get_user_model()


class AuditMixin(models.Model):
    """
    変更履歴を自動記録するためのMixin。

    このMixinを継承することで、モデルに自動的に履歴記録機能が追加されます。

    Example:
        >>> class MyModel(AuditMixin):
        ...     name = models.CharField(max_length=100)
        ...
        >>> obj = MyModel.objects.create(name="Test")
        >>> obj._history_user = request.user
        >>> obj._change_reason = "Created by user"
        >>> obj.name = "Updated"
        >>> obj.save()
        >>> # 履歴が自動的に記録される
    """

    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True


class AuditLog(models.Model):
    """
    カスタム監査ログモデル。

    アプリケーション固有のイベントを記録するためのモデルです。
    django-simple-historyとは別に、ビジネスロジックレベルのイベントを記録します。
    """

    # イベントタイプの選択肢
    EVENT_TYPE_CHOICES = [
        ("create", _("Created")),
        ("update", _("Updated")),
        ("delete", _("Deleted")),
        ("approve", _("Approved")),
        ("reject", _("Rejected")),
        ("submit", _("Submitted")),
        ("cancel", _("Cancelled")),
        ("custom", _("Custom")),
    ]

    # イベント情報
    event_type = models.CharField(
        _("Event Type"),
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
    )
    event_name = models.CharField(
        _("Event Name"),
        max_length=200,
        help_text=_("Human-readable event name"),
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Detailed description of the event"),
    )

    # 対象オブジェクト情報
    model_name = models.CharField(
        _("Model Name"),
        max_length=100,
        help_text=_("Name of the model that was changed"),
    )
    object_id = models.CharField(
        _("Object ID"),
        max_length=100,
        help_text=_("ID of the object that was changed"),
    )
    object_repr = models.CharField(
        _("Object Representation"),
        max_length=200,
        help_text=_("String representation of the object"),
    )

    # 変更内容
    changes = models.JSONField(
        _("Changes"),
        default=dict,
        blank=True,
        help_text=_("Dictionary of field changes"),
    )

    # メタデータ
    metadata = models.JSONField(
        _("Metadata"),
        default=dict,
        blank=True,
        help_text=_("Additional metadata"),
    )

    # ユーザー情報
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        verbose_name=_("User"),
    )
    user_ip = models.GenericIPAddressField(
        _("User IP Address"),
        null=True,
        blank=True,
    )
    user_agent = models.TextField(
        _("User Agent"),
        blank=True,
    )

    # タイムスタンプ
    created_at = models.DateTimeField(
        _("Created at"),
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        verbose_name = _("監査ログ")
        verbose_name_plural = _("監査ログ")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["model_name", "object_id"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.event_name} - {self.object_repr} ({self.created_at})"

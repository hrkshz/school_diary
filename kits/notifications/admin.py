"""
Django管理画面設定
"""
from django import forms
from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Notification
from .models import NotificationTemplate
from .models import NotificationType
from .tasks import send_notification_task


class NotificationTemplateForm(forms.ModelForm):
    """通知テンプレートのフォーム"""

    notification_types = forms.MultipleChoiceField(
        choices=NotificationType.choices,
        widget=forms.CheckboxSelectMultiple,
        label="通知タイプ",
        help_text="このテンプレートが対応する通知タイプ",
    )

    class Meta:
        model = NotificationTemplate
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 既存の値を設定
        if self.instance.pk and self.instance.notification_types:
            self.fields["notification_types"].initial = self.instance.notification_types


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """通知テンプレート管理画面"""

    form = NotificationTemplateForm
    list_display = [
        "code",
        "name",
        "types_display",
        "is_active",
        "usage_count",
        "updated_at",
    ]
    list_filter = ["is_active", "notification_types", "updated_at"]
    search_fields = ["code", "name", "description"]
    readonly_fields = ["created_at", "updated_at", "usage_count"]

    fieldsets = (
        ("基本情報", {
            "fields": ("code", "name", "description", "is_active"),
        }),
        ("テンプレート", {
            "fields": ("subject_template", "body_template", "html_template"),
        }),
        ("設定", {
            "fields": ("notification_types",),
        }),
        ("メタ情報", {
            "fields": ("usage_count", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="通知タイプ")
    def types_display(self, obj):
        """通知タイプを表示"""
        return ", ".join(obj.notification_types)

    @admin.display(description="使用回数")
    def usage_count(self, obj):
        """使用回数を表示"""
        count = obj.notifications.count()
        base_url = reverse("admin:notifications_notification_changelist")
        url = f"{base_url}?template__id__exact={obj.id}"
        return format_html('<a href="{}">{} 件</a>', url, count)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """通知管理画面"""

    list_display = [
        "id",
        "recipient",
        "subject",
        "notification_type",
        "priority",
        "status_badge",
        "sent_at",
        "read_at",
    ]
    list_filter = [
        "notification_type",
        "priority",
        "status",
        "sent_at",
        "created_at",
    ]
    search_fields = [
        "recipient__email",
        "recipient__name",
        "subject",
        "body",
    ]
    readonly_fields = [
        "template",
        "context_data_display",
        "created_at",
        "updated_at",
        "sent_at",
        "read_at",
        "retry_count",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        ("受信者情報", {
            "fields": ("recipient", "recipient_email"),
        }),
        ("通知内容", {
            "fields": (
                "notification_type",
                "priority",
                "template",
                "subject",
                "body",
                "html_body",
            ),
        }),
        ("ステータス", {
            "fields": (
                "status",
                "scheduled_at",
                "sent_at",
                "read_at",
                "error_message",
                "retry_count",
            ),
        }),
        ("関連情報", {
            "fields": (
                "related_object_type",
                "related_object_id",
                "context_data_display",
            ),
            "classes": ("collapse",),
        }),
        ("メタ情報", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    actions = ["resend_notifications", "mark_as_read"]

    @admin.display(description="ステータス")
    def status_badge(self, obj):
        """ステータスをバッジ表示"""
        colors = {
            "pending": "gray",
            "sending": "blue",
            "sent": "green",
            "failed": "red",
            "read": "purple",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="コンテキストデータ")
    def context_data_display(self, obj):
        """コンテキストデータを整形表示"""
        import json

        formatted_json = json.dumps(obj.context_data, indent=2, ensure_ascii=False)
        return mark_safe(f"<pre>{formatted_json}</pre>")

    @admin.action(description="選択した通知を再送信")
    def resend_notifications(self, request, queryset):
        """選択した通知を再送信"""
        count = 0
        for notification in queryset:
            if notification.status in ["failed", "pending"]:
                send_notification_task.delay(notification.id)  # type: ignore[misc]
                count += 1

        self.message_user(request, f"{count}件の通知を再送信キューに追加しました。")

    @admin.action(description="選択した通知を既読にする")
    def mark_as_read(self, request, queryset):
        """選択した通知を既読にする"""
        count = queryset.filter(status="sent").update(
            status="read",
            read_at=timezone.now(),
        )
        self.message_user(request, f"{count}件の通知を既読にしました。")

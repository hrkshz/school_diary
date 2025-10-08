"""
Audit trail admin interface.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from kits.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model."""

    list_display = [
        "id",
        "created_at_display",
        "event_type_display",
        "event_name",
        "object_info",
        "user_display",
    ]

    list_filter = [
        "event_type",
        "model_name",
        "created_at",
    ]

    search_fields = [
        "event_name",
        "description",
        "object_repr",
        "model_name",
        "object_id",
        "user__username",
        "user__email",
    ]

    readonly_fields = [
        "event_type",
        "event_name",
        "description",
        "model_name",
        "object_id",
        "object_repr",
        "changes_display",
        "metadata_display",
        "user",
        "user_ip",
        "user_agent",
        "created_at",
    ]

    date_hierarchy = "created_at"

    fieldsets = [
        (
            _("Event Information"),
            {
                "fields": [
                    "event_type",
                    "event_name",
                    "description",
                    "created_at",
                ],
            },
        ),
        (
            _("Object Information"),
            {
                "fields": [
                    "model_name",
                    "object_id",
                    "object_repr",
                ],
            },
        ),
        (
            _("Changes"),
            {
                "fields": [
                    "changes_display",
                    "metadata_display",
                ],
            },
        ),
        (
            _("User Information"),
            {
                "fields": [
                    "user",
                    "user_ip",
                    "user_agent",
                ],
            },
        ),
    ]

    def has_add_permission(self, request):
        """監査ログは手動で追加できない。"""
        return False

    def has_change_permission(self, request, obj=None):
        """監査ログは変更できない。"""
        return False

    def has_delete_permission(self, request, obj=None):
        """監査ログは削除できない（管理者のみ可能にする場合はここを変更）。"""
        return request.user.is_superuser

    @admin.display(description=_("Created At"), ordering="created_at")
    def created_at_display(self, obj):
        """作成日時の表示。"""
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

    @admin.display(description=_("Event Type"))
    def event_type_display(self, obj):
        """イベントタイプの表示（色付き）。"""
        colors = {
            "create": "#28a745",  # 緑
            "update": "#007bff",  # 青
            "delete": "#dc3545",  # 赤
            "approve": "#28a745",  # 緑
            "reject": "#ffc107",  # 黄
            "submit": "#17a2b8",  # シアン
            "cancel": "#6c757d",  # グレー
            "custom": "#6f42c1",  # 紫
        }

        color = colors.get(obj.event_type, "#000000")

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_event_type_display(),
        )

    @admin.display(description=_("Object"))
    def object_info(self, obj):
        """オブジェクト情報の表示。"""
        return format_html(
            "<strong>{}</strong><br><small>ID: {}</small>",
            obj.object_repr,
            obj.object_id,
        )

    @admin.display(description=_("User"))
    def user_display(self, obj):
        """ユーザー情報の表示。"""
        if obj.user:
            return format_html(
                "{}<br><small>{}</small>",
                obj.user.get_full_name() or obj.user.username,
                obj.user.email,
            )
        return _("Anonymous")

    @admin.display(description=_("Changes"))
    def changes_display(self, obj):
        """変更内容の表示（整形済み）。"""
        if not obj.changes:
            return _("No changes recorded")

        html_parts = []
        for field, change in obj.changes.items():
            if isinstance(change, dict) and "old" in change and "new" in change:
                html_parts.append(
                    f"<strong>{field}:</strong> "
                    f"<span style='color: red;'>{change['old']}</span> → "
                    f"<span style='color: green;'>{change['new']}</span>",
                )
            else:
                html_parts.append(f"<strong>{field}:</strong> {change}")

        return format_html("<br>".join(html_parts))

    @admin.display(description=_("Metadata"))
    def metadata_display(self, obj):
        """メタデータの表示（整形済み）。"""
        if not obj.metadata:
            return _("No metadata")

        html_parts = []
        for key, value in obj.metadata.items():
            html_parts.append(f"<strong>{key}:</strong> {value}")

        return format_html("<br>".join(html_parts))

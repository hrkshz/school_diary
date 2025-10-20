"""
承認フローのDjango管理画面設定。
"""

from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin

from kits.approvals.models import ApprovalAction
from kits.approvals.models import ApprovalRequest
from kits.approvals.models import ApprovalStep
from kits.approvals.models import ApprovalWorkflow


class ApprovalStepInline(admin.TabularInline):
    """承認ステップのインライン表示。"""

    model = ApprovalStep
    extra = 1
    fields = [
        "order",
        "name",
        "approver_role",
        "is_parallel",
        "required_approvals",
        "auto_approve_if_requester_in_role",
    ]
    ordering = ["order"]


@admin.register(ApprovalWorkflow)
class ApprovalWorkflowAdmin(SimpleHistoryAdmin):
    """承認ワークフローの管理画面。"""

    list_display = [
        "name",
        "is_active",
        "default_deadline_hours",
        "steps_count",
        "created_at",
    ]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    inlines = [ApprovalStepInline]

    fieldsets = [
        (
            "Basic Information",
            {
                "fields": ["name", "description", "is_active"],
            },
        ),
        (
            "Settings",
            {
                "fields": ["default_deadline_hours"],
            },
        ),
        (
            "Metadata",
            {
                "fields": ["created_by"],
                "classes": ["collapse"],
            },
        ),
    ]

    readonly_fields = []

    @admin.display(description="Steps")
    def steps_count(self, obj):
        """ステップ数を表示する。"""
        return obj.steps.count()

    def save_model(self, request, obj, form, change):
        """保存時にcreated_byを自動設定する。"""
        if not change:  # 新規作成時のみ
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ApprovalStep)
class ApprovalStepAdmin(admin.ModelAdmin):
    """承認ステップの管理画面。"""

    list_display = [
        "workflow",
        "order",
        "name",
        "approver_role",
        "is_parallel",
        "required_approvals",
    ]
    list_filter = ["workflow", "approver_role", "is_parallel"]
    search_fields = ["name", "description"]

    fieldsets = [
        (
            "Basic Information",
            {
                "fields": ["workflow", "order", "name", "description"],
            },
        ),
        (
            "Approval Settings",
            {
                "fields": [
                    "approver_role",
                    "is_parallel",
                    "required_approvals",
                    "auto_approve_if_requester_in_role",
                ],
            },
        ),
    ]


class ApprovalActionInline(admin.TabularInline):
    """承認アクションのインライン表示。"""

    model = ApprovalAction
    extra = 0
    fields = ["step", "approver", "action", "comment", "created_at"]
    readonly_fields = ["step", "approver", "action", "comment", "created_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        """追加権限なし（アクションは自動記録）。"""
        return False


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(SimpleHistoryAdmin):
    """承認依頼の管理画面。"""

    list_display = [
        "id",
        "workflow",
        "requester",
        "status_badge",
        "current_step",
        "requested_at",
        "deadline_status",
        "created_at",
    ]
    list_filter = [
        "status",
        "workflow",
        "requested_at",
        "created_at",
    ]
    search_fields = [
        "requester__username",
        "requester__email",
        "metadata",
    ]
    inlines = [ApprovalActionInline]

    fieldsets = [
        (
            "Request Information",
            {
                "fields": [
                    "workflow",
                    "requester",
                    "status",
                    "current_step",
                ],
            },
        ),
        (
            "Target Object",
            {
                "fields": [
                    "content_type",
                    "object_id",
                    "content_object_link",
                ],
            },
        ),
        (
            "Timeline",
            {
                "fields": [
                    "requested_at",
                    "deadline",
                    "completed_at",
                ],
            },
        ),
        (
            "Additional Information",
            {
                "fields": ["metadata"],
                "classes": ["collapse"],
            },
        ),
    ]

    readonly_fields = [
        "requested_at",
        "completed_at",
        "content_object_link",
    ]

    @admin.display(description="Status")
    def status_badge(self, obj):
        """ステータスをバッジで表示する。"""
        colors = {
            "draft": "gray",
            "pending": "orange",
            "approved": "green",
            "rejected": "red",
            "cancelled": "gray",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="Deadline")
    def deadline_status(self, obj):
        """期限の状態を表示する。"""
        if not obj.deadline:
            return "-"

        if obj.is_overdue():
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ Overdue</span>',
            )

        return obj.deadline.strftime("%Y-%m-%d %H:%M")

    @admin.display(description="Content Object")
    def content_object_link(self, obj):
        """承認対象オブジェクトへのリンクを表示する。"""
        if obj.content_object:
            return format_html(
                '<a href="/admin/{}/{}/{}/" target="_blank">{}</a>',
                obj.content_type.app_label,
                obj.content_type.model,
                obj.object_id,
                str(obj.content_object),
            )
        return "-"

    def get_readonly_fields(self, request, obj=None):
        """編集時は特定のフィールドを読み取り専用にする。"""
        readonly = list(self.readonly_fields)

        if obj:  # 編集時
            readonly.extend(["workflow", "requester", "content_type", "object_id"])

        return readonly


@admin.register(ApprovalAction)
class ApprovalActionAdmin(admin.ModelAdmin):
    """承認アクションの管理画面。"""

    list_display = [
        "request",
        "step",
        "approver",
        "action_badge",
        "created_at",
    ]
    list_filter = ["action", "step__workflow", "created_at"]
    search_fields = [
        "approver__username",
        "approver__email",
        "comment",
    ]

    fieldsets = [
        (
            "Action Information",
            {
                "fields": [
                    "request",
                    "step",
                    "approver",
                    "action",
                ],
            },
        ),
        (
            "Details",
            {
                "fields": ["comment", "created_at"],
            },
        ),
    ]

    readonly_fields = ["created_at"]

    @admin.display(description="Action")
    def action_badge(self, obj):
        """アクションをバッジで表示する。"""
        colors = {
            "approve": "green",
            "reject": "red",
            "return": "orange",
        }
        color = colors.get(obj.action, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_action_display(),
        )

    def has_add_permission(self, request):
        """管理画面から直接追加できないようにする。"""
        return False

    def has_change_permission(self, request, obj=None):
        """管理画面から変更できないようにする。"""
        return False

    def has_delete_permission(self, request, obj=None):
        """管理画面から削除できないようにする。"""
        return False

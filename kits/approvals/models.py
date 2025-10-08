"""
承認フロー管理システムのデータモデル。

このモジュールは、汎用的な承認ワークフローシステムを提供します。
どのようなモデルにも承認フローを追加できるよう、GenericForeignKeyを使用しています。
"""

from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from django.contrib.auth.models import Group

    User = AbstractUser
else:
    from django.contrib.auth import get_user_model

    User = get_user_model()


class ApprovalWorkflow(models.Model):
    """
    承認ワークフローのテンプレート。

    承認フローの定義（例: 2段階承認、3段階承認）を管理します。
    複数のApprovalStepを持ち、承認の流れを定義します。
    """

    name = models.CharField(_("Workflow Name"), max_length=200, unique=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)

    # 承認期限設定（時間単位）
    default_deadline_hours = models.PositiveIntegerField(
        _("Default Deadline (hours)"),
        default=72,
        help_text=_("Default deadline for approval in hours"),
    )

    # メタデータ
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_workflows",
        verbose_name=_("Created by"),
    )

    # 履歴管理
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("承認ワークフロー")
        verbose_name_plural = _("承認ワークフロー")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_steps(self):
        """このワークフローの全ステップを順序通りに取得する。"""
        return self.steps.order_by("order")

    def get_first_step(self):
        """最初のステップを取得する。"""
        return self.steps.order_by("order").first()


class ApprovalStep(models.Model):
    """
    承認ステップの定義。

    ワークフロー内の1つの承認ステップを表します。
    各ステップには承認者のロール（Group）が設定されます。
    """

    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.CASCADE,
        related_name="steps",
        verbose_name=_("Workflow"),
    )
    order = models.PositiveIntegerField(_("Order"), default=1)
    name = models.CharField(_("Step Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)

    # 承認者のロール（django.contrib.auth.models.Group）
    approver_role = models.ForeignKey(
        "auth.Group",
        on_delete=models.CASCADE,
        related_name="approval_steps",
        verbose_name=_("Approver Role"),
        help_text=_("Group that can approve this step"),
    )

    # 並列承認の設定
    is_parallel = models.BooleanField(
        _("Is Parallel"),
        default=False,
        help_text=_("If True, multiple approvers can approve in parallel"),
    )
    required_approvals = models.PositiveIntegerField(
        _("Required Approvals"),
        default=1,
        help_text=_("Number of approvals required (for parallel approval)"),
    )

    # 自動承認の設定
    auto_approve_if_requester_in_role = models.BooleanField(
        _("Auto-approve if requester in role"),
        default=False,
        help_text=_(
            "If True, automatically approve if requester belongs to approver role"
        ),
    )

    class Meta:
        verbose_name = _("承認ステップ")
        verbose_name_plural = _("承認ステップ")
        ordering = ["workflow", "order"]
        unique_together = [["workflow", "order"]]

    def __str__(self):
        return f"{self.workflow.name} - Step {self.order}: {self.name}"

    def get_next_step(self):
        """次のステップを取得する。最後のステップの場合はNoneを返す。"""
        return (
            ApprovalStep.objects.filter(workflow=self.workflow, order__gt=self.order)
            .order_by("order")
            .first()
        )

    def can_approve(self, user: "User") -> bool:
        """指定されたユーザーがこのステップを承認できるかを判定する。"""
        return self.approver_role.user_set.filter(pk=user.pk).exists()


class ApprovalRequest(models.Model):
    """
    承認依頼。

    実際の承認リクエストを表します。
    GenericForeignKeyを使用して、任意のモデルに対する承認を管理できます。
    """

    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("pending", _("Pending")),
        ("approved", _("Approved")),
        ("rejected", _("Rejected")),
        ("cancelled", _("Cancelled")),
    ]

    # 使用するワークフロー
    workflow = models.ForeignKey(
        ApprovalWorkflow,
        on_delete=models.PROTECT,
        related_name="requests",
        verbose_name=_("Workflow"),
    )

    # 承認対象（GenericForeignKey）
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    # 申請者
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approval_requests",
        verbose_name=_("Requester"),
    )

    # ステータス
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default="draft"
    )

    # 現在のステップ
    current_step = models.ForeignKey(
        ApprovalStep,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="current_requests",
        verbose_name=_("Current Step"),
    )

    # 日時情報
    requested_at = models.DateTimeField(_("Requested at"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Completed at"), null=True, blank=True)
    deadline = models.DateTimeField(_("Deadline"), null=True, blank=True)

    # メタデータ
    metadata = models.JSONField(
        _("Metadata"), default=dict, blank=True, help_text=_("Additional information")
    )

    # タイムスタンプ
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    # 履歴管理
    history = HistoricalRecords()

    class Meta:
        verbose_name = _("承認申請")
        verbose_name_plural = _("承認申請")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["requester"]),
        ]

    def __str__(self):
        return f"{self.workflow.name} - {self.requester} - {self.get_status_display()}"

    def submit(self):
        """承認依頼を提出する。"""
        if self.status != "draft":
            msg = "Only draft requests can be submitted"
            raise ValueError(msg)

        self.status = "pending"
        self.requested_at = timezone.now()
        self.current_step = self.workflow.get_first_step()

        # デフォルトの期限を設定
        if not self.deadline and self.workflow.default_deadline_hours:
            self.deadline = timezone.now() + timezone.timedelta(
                hours=self.workflow.default_deadline_hours
            )

        self.save()

        # 自動承認のチェック
        if (
            self.current_step
            and self.current_step.auto_approve_if_requester_in_role
            and self.current_step.can_approve(self.requester)
        ):
            # 自動承認を実行（次のステップに進む）
            from kits.approvals.services import ApprovalService

            service = ApprovalService()
            service.auto_approve_step(self, self.current_step, self.requester)

    def cancel(self, user: "User"):
        """承認依頼をキャンセルする。"""
        if self.status not in ["draft", "pending"]:
            msg = "Only draft or pending requests can be cancelled"
            raise ValueError(msg)

        self.status = "cancelled"
        self.completed_at = timezone.now()
        self._history_user = user
        self._change_reason = "Cancelled by user"
        self.save()

    def is_overdue(self) -> bool:
        """期限切れかどうかを判定する。"""
        if not self.deadline or self.status not in ["pending"]:
            return False
        return timezone.now() > self.deadline

    def get_pending_approvers(self):
        """現在のステップで承認可能なユーザーを取得する。"""
        if not self.current_step:
            return User.objects.none()
        return self.current_step.approver_role.user_set.all()


class ApprovalAction(models.Model):
    """
    承認アクション履歴。

    承認、否認、差戻しなどのアクションを記録します。
    """

    ACTION_CHOICES = [
        ("approve", _("Approve")),
        ("reject", _("Reject")),
        ("return", _("Return to Requester")),
    ]

    request = models.ForeignKey(
        ApprovalRequest,
        on_delete=models.CASCADE,
        related_name="actions",
        verbose_name=_("Request"),
    )
    step = models.ForeignKey(
        ApprovalStep,
        on_delete=models.CASCADE,
        related_name="actions",
        verbose_name=_("Step"),
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approval_actions",
        verbose_name=_("Approver"),
    )

    action = models.CharField(_("Action"), max_length=20, choices=ACTION_CHOICES)
    comment = models.TextField(_("Comment"), blank=True)

    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("承認操作")
        verbose_name_plural = _("承認操作")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_action_display()} by {self.approver} at {self.step}"

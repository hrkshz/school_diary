"""
承認フローサービス層。

承認フローの制御、ステップ進行、通知などを管理します。
"""

import logging
from typing import TYPE_CHECKING

from django.db import transaction
from django.utils import timezone

from kits.approvals.models import ApprovalAction
from kits.approvals.models import ApprovalRequest
from kits.approvals.models import ApprovalStep

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

    User = AbstractUser
else:
    from django.contrib.auth import get_user_model

    User = get_user_model()

logger = logging.getLogger(__name__)


class ApprovalService:
    """
    承認フローを制御するサービスクラス。

    承認、否認、差戻し、自動ステップ進行などの機能を提供します。
    """

    def create_request(
        self, workflow, content_object, requester: "User", metadata: dict | None = None,
    ) -> ApprovalRequest:
        """
        承認依頼を作成する。

        Args:
            workflow: 使用する承認ワークフロー
            content_object: 承認対象のオブジェクト
            requester: 申請者
            metadata: 追加情報（オプション）

        Returns:
            ApprovalRequest: 作成された承認依頼

        Example:
            >>> service = ApprovalService()
            >>> request = service.create_request(
            ...     workflow=my_workflow,
            ...     content_object=my_document,
            ...     requester=user,
            ...     metadata={"priority": "high"}
            ... )
        """
        request = ApprovalRequest.objects.create(
            workflow=workflow,
            content_object=content_object,
            requester=requester,
            metadata=metadata or {},
            status="draft",
        )

        logger.info(
            "Created approval request %s for %s by %s",
            request.id,
            content_object,
            requester,
        )

        return request

    def submit_request(self, request: ApprovalRequest) -> ApprovalRequest:
        """
        承認依頼を提出する。

        Args:
            request: 提出する承認依頼

        Returns:
            ApprovalRequest: 更新された承認依頼

        Raises:
            ValueError: draft状態でない場合
        """
        with transaction.atomic():
            request.submit()

            logger.info(
                "Submitted approval request %s, current step: %s",
                request.id,
                request.current_step,
            )

            # 通知を送信（kits.notificationsが利用可能な場合）
            self._send_notification(
                request, "approval_request_submitted", request.requester,
            )

            if request.current_step:
                self._notify_approvers(request, request.current_step)

        return request

    @transaction.atomic
    def approve_step(
        self, request: ApprovalRequest, step: ApprovalStep, approver: "User", comment: str = "",
    ) -> ApprovalRequest:
        """
        承認ステップを承認する。

        Args:
            request: 承認依頼
            step: 承認するステップ
            approver: 承認者
            comment: コメント（オプション）

        Returns:
            ApprovalRequest: 更新された承認依頼

        Raises:
            ValueError: 承認できない場合
        """
        # 権限チェック
        if not step.can_approve(approver):
            msg = f"User {approver} is not authorized to approve step {step}"
            raise ValueError(msg)

        # ステップチェック
        if request.current_step != step:
            msg = f"Current step is {request.current_step}, not {step}"
            raise ValueError(msg)

        # 承認アクションを記録
        action = ApprovalAction.objects.create(
            request=request, step=step, approver=approver, action="approve", comment=comment,
        )

        logger.info("Created approval action %s for request %s", action.id, request.id)

        # 並列承認の場合、必要承認数をチェック
        if step.is_parallel:
            approval_count = ApprovalAction.objects.filter(
                request=request, step=step, action="approve",
            ).count()

            if approval_count < step.required_approvals:
                logger.info(
                    "Parallel approval: %s/%s approvals received for request %s",
                    approval_count,
                    step.required_approvals,
                    request.id,
                )
                return request

        # 次のステップへ進む
        next_step = step.get_next_step()

        if next_step:
            # 次のステップへ
            request.current_step = next_step
            request._history_user = approver
            request._change_reason = f"Approved step {step.order}: {step.name}"
            request.save()

            logger.info(
                "Request %s advanced to step %s", request.id, next_step.order,
            )

            # 自動承認のチェック
            if (
                next_step.auto_approve_if_requester_in_role
                and next_step.can_approve(request.requester)
            ):
                self.auto_approve_step(request, next_step, request.requester)
            else:
                # 次のステップの承認者に通知
                self._notify_approvers(request, next_step)
        else:
            # 全ステップ完了
            request.status = "approved"
            request.completed_at = timezone.now()
            request.current_step = None
            request._history_user = approver
            request._change_reason = "All steps approved"
            request.save()

            logger.info("Request %s fully approved", request.id)

            # 申請者に完了通知
            self._send_notification(request, "approval_request_approved", approver)

        return request

    @transaction.atomic
    def reject_step(
        self, request: ApprovalRequest, step: ApprovalStep, approver: "User", comment: str = "",
    ) -> ApprovalRequest:
        """
        承認ステップを否認する。

        Args:
            request: 承認依頼
            step: 否認するステップ
            approver: 否認者
            comment: コメント（必須推奨）

        Returns:
            ApprovalRequest: 更新された承認依頼

        Raises:
            ValueError: 否認できない場合
        """
        # 権限チェック
        if not step.can_approve(approver):
            msg = f"User {approver} is not authorized to reject step {step}"
            raise ValueError(msg)

        # ステップチェック
        if request.current_step != step:
            msg = f"Current step is {request.current_step}, not {step}"
            raise ValueError(msg)

        # 否認アクションを記録
        action = ApprovalAction.objects.create(
            request=request, step=step, approver=approver, action="reject", comment=comment,
        )

        logger.info("Created rejection action %s for request %s", action.id, request.id)

        # リクエストを否認状態に
        request.status = "rejected"
        request.completed_at = timezone.now()
        request.current_step = None
        request._history_user = approver
        request._change_reason = f"Rejected at step {step.order}: {step.name}"
        request.save()

        logger.info("Request %s rejected at step %s", request.id, step.order)

        # 申請者に通知
        self._send_notification(request, "approval_request_rejected", approver)

        return request

    @transaction.atomic
    def return_to_requester(
        self, request: ApprovalRequest, step: ApprovalStep, approver: "User", comment: str = "",
    ) -> ApprovalRequest:
        """
        承認依頼を申請者に差戻す。

        Args:
            request: 承認依頼
            step: 差戻すステップ
            approver: 差戻す人
            comment: コメント（必須推奨）

        Returns:
            ApprovalRequest: 更新された承認依頼

        Raises:
            ValueError: 差戻せない場合
        """
        # 権限チェック
        if not step.can_approve(approver):
            msg = f"User {approver} is not authorized to return step {step}"
            raise ValueError(msg)

        # ステップチェック
        if request.current_step != step:
            msg = f"Current step is {request.current_step}, not {step}"
            raise ValueError(msg)

        # 差戻しアクションを記録
        action = ApprovalAction.objects.create(
            request=request, step=step, approver=approver, action="return", comment=comment,
        )

        logger.info(
            "Created return action %s for request %s", action.id, request.id,
        )

        # リクエストをdraft状態に戻す
        request.status = "draft"
        request.current_step = None
        request.requested_at = None
        request.deadline = None
        request._history_user = approver
        request._change_reason = f"Returned to requester from step {step.order}: {step.name}"
        request.save()

        logger.info("Request %s returned to requester", request.id)

        # 申請者に通知
        self._send_notification(request, "approval_request_returned", approver)

        return request

    def auto_approve_step(
        self, request: ApprovalRequest, step: ApprovalStep, user: "User",
    ) -> ApprovalRequest:
        """
        ステップを自動承認する。

        申請者が承認者ロールに属している場合の自動承認処理。

        Args:
            request: 承認依頼
            step: 自動承認するステップ
            user: 自動承認を実行するユーザー

        Returns:
            ApprovalRequest: 更新された承認依頼
        """
        logger.info(
            "Auto-approving step %s for request %s", step.order, request.id,
        )

        return self.approve_step(
            request, step, user, comment="Auto-approved (requester in approver role)",
        )

    def get_pending_requests_for_user(self, user: "User"):
        """
        ユーザーが承認可能な保留中のリクエストを取得する。

        Args:
            user: ユーザー

        Returns:
            QuerySet: 承認可能な承認依頼のクエリセット
        """
        # ユーザーが所属するグループを取得
        user_groups = user.groups.all()

        # 承認可能なステップを取得
        approver_steps = ApprovalStep.objects.filter(approver_role__in=user_groups)

        # 保留中で、ユーザーが承認可能なリクエストを取得
        return ApprovalRequest.objects.filter(
            status="pending", current_step__in=approver_steps,
        ).distinct()

    def get_overdue_requests(self):
        """
        期限切れの承認依頼を取得する。

        Returns:
            QuerySet: 期限切れの承認依頼のクエリセット
        """
        now = timezone.now()
        return ApprovalRequest.objects.filter(
            status="pending", deadline__lt=now,
        )

    def _send_notification(self, request: ApprovalRequest, template_code: str, actor: "User"):
        """
        通知を送信する（kits.notificationsが利用可能な場合）。

        Args:
            request: 承認依頼
            template_code: 通知テンプレートコード
            actor: アクションを実行したユーザー
        """
        try:
            from kits.notifications.services import NotificationService

            service = NotificationService()

            # 申請者に通知
            context = {
                "request_id": request.id,
                "workflow_name": request.workflow.name,
                "actor_name": actor.get_full_name() or actor.username,
                "content_object": str(request.content_object),
            }

            service.create_from_template(
                template_code=template_code,
                recipient=request.requester,
                context=context,
                related_object_type="approval_request",
                related_object_id=str(request.id),
            )

            logger.info(
                "Sent notification %s to %s for request %s",
                template_code,
                request.requester,
                request.id,
            )

        except (ImportError, Exception) as e:
            logger.debug("Could not send notification: %s", e)

    def _notify_approvers(self, request: ApprovalRequest, step: ApprovalStep):
        """
        承認者に通知を送信する。

        Args:
            request: 承認依頼
            step: 通知対象のステップ
        """
        try:
            from kits.notifications.services import NotificationService

            service = NotificationService()

            # 承認可能なユーザーに通知
            approvers = step.approver_role.user_set.all()

            context = {
                "request_id": request.id,
                "workflow_name": request.workflow.name,
                "step_name": step.name,
                "requester_name": request.requester.get_full_name()
                or request.requester.username,
                "content_object": str(request.content_object),
            }

            for approver in approvers:
                service.create_from_template(
                    template_code="approval_request_pending",
                    recipient=approver,
                    context=context,
                    related_object_type="approval_request",
                    related_object_id=str(request.id),
                )

            logger.info(
                "Notified %s approvers for request %s, step %s",
                approvers.count(),
                request.id,
                step.order,
            )

        except (ImportError, Exception) as e:
            logger.debug("Could not notify approvers: %s", e)

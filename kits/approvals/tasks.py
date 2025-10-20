"""
承認フロー用のCeleryタスク。

承認期限のチェック、リマインダー送信などの定期タスクを提供します。
"""

import logging

from celery import shared_task
from django.utils import timezone

from kits.approvals.models import ApprovalRequest
from kits.approvals.services import ApprovalService

logger = logging.getLogger(__name__)


@shared_task(name="kits.approvals.check_overdue_requests")
def check_overdue_requests():
    """
    期限切れの承認依頼をチェックし、通知を送信する。

    定期実行（例: 1時間ごと）を推奨。

    Returns:
        dict: 実行結果の統計情報
    """
    logger.info("Starting check_overdue_requests task")

    service = ApprovalService()
    overdue_requests = service.get_overdue_requests()

    count = 0
    for request in overdue_requests:
        try:
            # 期限切れ通知を送信
            _send_overdue_notification(request)
            count += 1

        except Exception:
            logger.exception(
                "Failed to send overdue notification for request %s",
                request.id,
            )

    logger.info("Checked %s overdue requests, sent %s notifications", overdue_requests.count(), count)

    return {"checked": overdue_requests.count(), "notified": count}


@shared_task(name="kits.approvals.send_reminder_notifications")
def send_reminder_notifications(hours_before_deadline: int = 24):
    """
    期限が近づいている承認依頼のリマインダーを送信する。

    Args:
        hours_before_deadline: 期限の何時間前にリマインダーを送信するか（デフォルト: 24時間）

    Returns:
        dict: 実行結果の統計情報
    """
    logger.info(
        "Starting send_reminder_notifications task (hours_before_deadline=%s)",
        hours_before_deadline,
    )

    now = timezone.now()
    reminder_threshold = now + timezone.timedelta(hours=hours_before_deadline)

    # 期限が近い保留中のリクエストを取得
    upcoming_requests = ApprovalRequest.objects.filter(
        status="pending",
        deadline__lte=reminder_threshold,
        deadline__gt=now,
    )

    count = 0
    for request in upcoming_requests:
        try:
            # リマインダー通知を送信
            _send_reminder_notification(request, hours_before_deadline)
            count += 1

        except Exception:
            logger.exception(
                "Failed to send reminder notification for request %s",
                request.id,
            )

    logger.info("Sent %s reminder notifications", count)

    return {"checked": upcoming_requests.count(), "notified": count}


@shared_task(name="kits.approvals.auto_escalate_overdue_requests")
def auto_escalate_overdue_requests(max_overdue_hours: int = 72):
    """
    期限切れの承認依頼を自動的にエスカレーションする。

    Args:
        max_overdue_hours: 期限超過後、何時間後にエスカレーションするか（デフォルト: 72時間）

    Returns:
        dict: 実行結果の統計情報

    Note:
        エスカレーションロジックはプロジェクトごとにカスタマイズが必要です。
        このタスクはテンプレートとして提供されています。
    """
    logger.info(
        "Starting auto_escalate_overdue_requests task (max_overdue_hours=%s)",
        max_overdue_hours,
    )

    now = timezone.now()
    escalation_threshold = now - timezone.timedelta(hours=max_overdue_hours)

    # 長期間期限切れのリクエストを取得
    long_overdue_requests = ApprovalRequest.objects.filter(
        status="pending",
        deadline__lt=escalation_threshold,
    )

    count = 0
    for request in long_overdue_requests:
        try:
            # エスカレーション通知を送信（管理者など）
            _send_escalation_notification(request)
            count += 1

        except Exception:
            logger.exception(
                "Failed to send escalation notification for request %s",
                request.id,
            )

    logger.info("Escalated %s requests", count)

    return {"checked": long_overdue_requests.count(), "escalated": count}


def _send_overdue_notification(request: ApprovalRequest):
    """
    期限切れ通知を送信する内部関数。

    Args:
        request: 承認依頼
    """
    try:
        from kits.notifications.services import NotificationService

        service = NotificationService()

        # 申請者に通知
        context = {
            "request_id": request.id,
            "workflow_name": request.workflow.name,
            "deadline": request.deadline.strftime("%Y-%m-%d %H:%M") if request.deadline else "N/A",
            "content_object": str(request.content_object),
        }

        service.create_from_template(
            template_code="approval_request_overdue",
            recipient=request.requester,
            context=context,
            related_object_type="approval_request",
            related_object_id=str(request.id),
        )

        # 現在のステップの承認者にも通知
        if request.current_step:
            approvers = request.current_step.approver_role.user_set.all()
            for approver in approvers:
                service.create_from_template(
                    template_code="approval_request_overdue_approver",
                    recipient=approver,
                    context=context,
                    related_object_type="approval_request",
                    related_object_id=str(request.id),
                )

        logger.info("Sent overdue notification for request %s", request.id)

    except ImportError:
        logger.debug("kits.notifications not available, skipping notification")


def _send_reminder_notification(request: ApprovalRequest, hours_before: int):
    """
    リマインダー通知を送信する内部関数。

    Args:
        request: 承認依頼
        hours_before: 期限の何時間前か
    """
    try:
        from kits.notifications.services import NotificationService

        service = NotificationService()

        if request.current_step:
            approvers = request.current_step.approver_role.user_set.all()

            context = {
                "request_id": request.id,
                "workflow_name": request.workflow.name,
                "step_name": request.current_step.name,
                "hours_before": hours_before,
                "deadline": request.deadline.strftime("%Y-%m-%d %H:%M") if request.deadline else "N/A",
                "content_object": str(request.content_object),
            }

            for approver in approvers:
                service.create_from_template(
                    template_code="approval_request_reminder",
                    recipient=approver,
                    context=context,
                    related_object_type="approval_request",
                    related_object_id=str(request.id),
                )

        logger.info("Sent reminder notification for request %s", request.id)

    except ImportError:
        logger.debug("kits.notifications not available, skipping notification")


def _send_escalation_notification(request: ApprovalRequest):
    """
    エスカレーション通知を送信する内部関数。

    Args:
        request: 承認依頼

    Note:
        デフォルトでは管理者に通知を送ります。
        プロジェクトごとにカスタマイズが必要です。
    """
    try:
        from django.contrib.auth import get_user_model

        from kits.notifications.services import NotificationService

        User = get_user_model()
        service = NotificationService()

        # 管理者（is_staff=True）を取得
        admins = User.objects.filter(is_staff=True)

        context = {
            "request_id": request.id,
            "workflow_name": request.workflow.name,
            "requester_name": request.requester.get_full_name() or request.requester.username,
            "deadline": request.deadline.strftime("%Y-%m-%d %H:%M") if request.deadline else "N/A",
            "content_object": str(request.content_object),
        }

        for admin in admins:
            service.create_from_template(
                template_code="approval_request_escalation",
                recipient=admin,
                context=context,
                related_object_type="approval_request",
                related_object_id=str(request.id),
            )

        logger.info("Sent escalation notification for request %s", request.id)

    except ImportError:
        logger.debug("kits.notifications not available, skipping notification")

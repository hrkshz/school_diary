"""
Celeryタスク

通知の非同期送信を担当します。
"""
import logging

from celery import shared_task
from django.db.models import Q
from django.utils import timezone

from .models import Notification
from .models import NotificationStatus
from .services import NotificationService

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1分後にリトライ
)
def send_notification_task(self, notification_id: int):
    """
    通知を非同期で送信

    Args:
        notification_id: 送信する通知のID
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        service = NotificationService()
        success = service.send_notification(notification)

        if not success and notification.can_retry:
            # リトライ可能な場合は再試行
            raise self.retry(countdown=60 * (notification.retry_count + 1))

        return {
            "notification_id": notification_id,
            "status": notification.status,
            "success": success,
        }

    except Notification.DoesNotExist:
        logger.exception(f"通知が見つかりません: ID={notification_id}")
        return {"error": "Notification not found"}

    except Exception as e:
        logger.exception(f"通知送信エラー: {notification_id} - {e!s}")
        raise


@shared_task
def send_scheduled_notifications():
    """
    送信予定の通知を一括送信

    スケジュールされた通知のうち、送信時刻を過ぎたものを送信します。
    Celery Beatで定期実行することを想定(例: 5分ごと)
    """
    now = timezone.now()

    # 送信対象の通知を取得
    notifications = Notification.objects.filter(
        Q(scheduled_at__lte=now) | Q(scheduled_at__isnull=True),
        status=NotificationStatus.PENDING,
    ).order_by("priority", "created_at")[:100]  # 最大100件

    logger.info(f"送信対象の通知: {notifications.count()}件")

    # 各通知を非同期タスクとして送信
    for notification in notifications:
        send_notification_task.delay(notification.id)  # type: ignore[misc]

    return {
        "processed": notifications.count(),
        "timestamp": now.isoformat(),
    }


@shared_task
def cleanup_old_notifications(retention_days: int = 90):
    """
    古い通知を削除

    Args:
        retention_days: 保持期間(日数)

    送信済み・既読の通知のうち、retention_days日以上経過したものを削除します。
    """
    cutoff_date = timezone.now() - timezone.timedelta(days=retention_days)

    deleted_count, _ = Notification.objects.filter(
        status__in=[NotificationStatus.SENT, NotificationStatus.READ],
        created_at__lt=cutoff_date,
    ).delete()

    logger.info(f"古い通知を削除: {deleted_count}件")

    return {
        "deleted": deleted_count,
        "cutoff_date": cutoff_date.isoformat(),
    }


@shared_task
def retry_failed_notifications():
    """
    失敗した通知を再送信

    リトライ可能な失敗通知を再送信します。
    """
    from django.conf import settings
    max_retries = settings.NOTIFICATIONS_CONFIG.get("RETRY_ATTEMPTS", 3)

    # リトライ対象の通知を取得
    failed_notifications = Notification.objects.filter(
        status=NotificationStatus.FAILED,
        retry_count__lt=max_retries,
    )[:50]  # 最大50件

    logger.info(f"リトライ対象の通知: {failed_notifications.count()}件")

    for notification in failed_notifications:
        send_notification_task.delay(notification.id)  # type: ignore[misc]

    return {
        "retried": failed_notifications.count(),
    }

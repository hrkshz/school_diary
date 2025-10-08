"""
監査証跡の定期タスク。

古い履歴データのクリーンアップや、定期レポート生成などのタスクを提供します。
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from kits.audit.models import AuditLog

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_audit_logs(days: int = 365):
    """
    古い監査ログを削除する。

    Args:
        days: 何日より古いログを削除するか（デフォルト: 365日）

    Returns:
        int: 削除されたログの数

    Example:
        >>> from kits.audit.tasks import cleanup_old_audit_logs
        >>> cleanup_old_audit_logs.delay(days=180)
    """
    cutoff_date = timezone.now() - timedelta(days=days)

    # 削除対象のログを取得
    old_logs = AuditLog.objects.filter(created_at__lt=cutoff_date)
    count = old_logs.count()

    # 削除実行
    old_logs.delete()

    logger.info(
        "Cleaned up %d audit logs older than %d days (before %s)",
        count,
        days,
        cutoff_date,
    )

    return count


@shared_task
def cleanup_old_history_records(model_name: str, days: int = 365):
    """
    特定モデルの古い履歴レコードを削除する（django-simple-history）。

    Args:
        model_name: モデル名（例: "demo_request"）
        days: 何日より古い履歴を削除するか

    Returns:
        int: 削除された履歴レコードの数

    Note:
        この関数は慎重に使用してください。
        履歴は監査証跡として重要な情報です。

    Example:
        >>> from kits.audit.tasks import cleanup_old_history_records
        >>> cleanup_old_history_records.delay("demo_request", days=730)
    """
    from django.apps import apps

    cutoff_date = timezone.now() - timedelta(days=days)

    try:
        # モデルを取得
        model = None
        for app_config in apps.get_app_configs():
            try:
                model = apps.get_model(app_config.label, model_name)
                break
            except LookupError:
                continue

        if not model:
            logger.error("Model '%s' not found", model_name)
            return 0

        # 履歴モデルを取得
        if not hasattr(model, "history"):
            logger.warning("Model '%s' does not have history tracking", model_name)
            return 0

        history_model = model.history.model

        # 古い履歴を削除
        old_records = history_model.objects.filter(history_date__lt=cutoff_date)
        count = old_records.count()
        old_records.delete()

        logger.info(
            "Cleaned up %d history records for %s older than %d days",
            count,
            model_name,
            days,
        )

        return count

    except Exception as e:
        logger.error(
            "Error cleaning up history for %s: %s",
            model_name,
            str(e),
            exc_info=True,
        )
        return 0


@shared_task
def generate_daily_audit_report():
    """
    日次監査レポートを生成する。

    前日の監査ログをサマリーし、管理者にメール送信します。

    Returns:
        dict: レポートデータ

    Example:
        >>> from kits.audit.tasks import generate_daily_audit_report
        >>> generate_daily_audit_report.delay()
    """
    from kits.audit.services import AuditService

    # 前日の範囲を計算
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)

    # レポート生成
    service = AuditService()
    report = service.generate_audit_report(
        start_date=yesterday,
        end_date=today,
    )

    logger.info(
        "Generated daily audit report: %d events",
        report["total_events"],
    )

    # TODO: メール送信機能（kits.notificationsと統合）
    # if report['total_events'] > 0:
    #     send_admin_email(
    #         subject=f"Daily Audit Report - {yesterday.date()}",
    #         body=format_report(report)
    #     )

    return report


@shared_task
def generate_weekly_audit_report():
    """
    週次監査レポートを生成する。

    過去7日間の監査ログをサマリーし、管理者にメール送信します。

    Returns:
        dict: レポートデータ

    Example:
        >>> from kits.audit.tasks import generate_weekly_audit_report
        >>> generate_weekly_audit_report.delay()
    """
    from kits.audit.services import AuditService

    # 過去7日間の範囲を計算
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)

    # レポート生成
    service = AuditService()
    report = service.generate_audit_report(
        start_date=start_date,
        end_date=end_date,
    )

    logger.info(
        "Generated weekly audit report: %d events",
        report["total_events"],
    )

    # TODO: メール送信機能
    # if report['total_events'] > 0:
    #     send_admin_email(
    #         subject=f"Weekly Audit Report - {start_date.date()} to {end_date.date()}",
    #         body=format_report(report)
    #     )

    return report


@shared_task
def archive_old_audit_logs(days: int = 90, archive_path: str | None = None):
    """
    古い監査ログをアーカイブする（削除前にバックアップ）。

    Args:
        days: 何日より古いログをアーカイブするか
        archive_path: アーカイブファイルのパス（省略時は自動生成）

    Returns:
        dict: アーカイブ結果

    Note:
        この関数は大量のデータを扱う可能性があるため、
        実行時間に注意してください。

    Example:
        >>> from kits.audit.tasks import archive_old_audit_logs
        >>> archive_old_audit_logs.delay(days=90)
    """
    import csv
    from pathlib import Path

    cutoff_date = timezone.now() - timedelta(days=days)

    # アーカイブ対象のログを取得
    old_logs = AuditLog.objects.filter(created_at__lt=cutoff_date)
    count = old_logs.count()

    if count == 0:
        logger.info("No logs to archive")
        return {"archived": 0, "file": None}

    # アーカイブファイルのパスを決定
    if not archive_path:
        archive_dir = Path("/tmp/audit_archives")
        archive_dir.mkdir(exist_ok=True)
        archive_path = str(archive_dir / f"audit_logs_{cutoff_date.date()}.csv")

    # CSVにエクスポート
    with open(archive_path, "w", newline="") as csvfile:
        fieldnames = [
            "id",
            "created_at",
            "event_type",
            "event_name",
            "model_name",
            "object_id",
            "object_repr",
            "user",
            "description",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for log in old_logs.iterator():
            writer.writerow(
                {
                    "id": log.id,
                    "created_at": log.created_at,
                    "event_type": log.event_type,
                    "event_name": log.event_name,
                    "model_name": log.model_name,
                    "object_id": log.object_id,
                    "object_repr": log.object_repr,
                    "user": log.user.username if log.user else "",
                    "description": log.description,
                },
            )

    logger.info(
        "Archived %d audit logs to %s",
        count,
        archive_path,
    )

    # アーカイブ後、元のログを削除
    old_logs.delete()

    return {
        "archived": count,
        "file": str(archive_path),
    }

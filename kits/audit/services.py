"""
監査証跡サービス層。

履歴の検索、比較、レポート生成などの機能を提供します。
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING
from typing import Any

from django.db.models import Model
from django.utils import timezone

from kits.audit.models import AuditLog

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser

    User = AbstractUser
else:
    from django.contrib.auth import get_user_model

    User = get_user_model()

logger = logging.getLogger(__name__)


class AuditService:
    """
    監査証跡を管理するサービスクラス。

    履歴の記録、検索、比較、レポート生成などの機能を提供します。
    """

    def log_event(
        self,
        event_type: str,
        event_name: str,
        obj: Model,
        user: "User | None" = None,
        description: str = "",
        changes: dict | None = None,
        metadata: dict | None = None,
        user_ip: str | None = None,
        user_agent: str = "",
    ) -> AuditLog:
        """
        イベントをログに記録する。

        Args:
            event_type: イベントタイプ（create, update, delete等）
            event_name: イベント名（人間が読める形式）
            obj: 対象オブジェクト
            user: 実行したユーザー
            description: イベントの詳細説明
            changes: 変更内容の辞書
            metadata: 追加のメタデータ
            user_ip: ユーザーのIPアドレス
            user_agent: ユーザーエージェント

        Returns:
            AuditLog: 作成された監査ログ

        Example:
            >>> service = AuditService()
            >>> service.log_event(
            ...     event_type="approve",
            ...     event_name="残業申請承認",
            ...     obj=overtime_request,
            ...     user=manager,
            ...     description="課長が承認しました",
            ...     changes={"status": {"from": "pending", "to": "approved"}}
            ... )
        """
        log = AuditLog.objects.create(
            event_type=event_type,
            event_name=event_name,
            model_name=obj._meta.model_name,
            object_id=str(obj.pk),
            object_repr=str(obj),
            description=description,
            changes=changes or {},
            metadata=metadata or {},
            user=user,
            user_ip=user_ip,
            user_agent=user_agent,
        )

        logger.info(
            "Logged audit event: %s for %s (id=%s) by %s",
            event_name,
            obj._meta.model_name,
            obj.pk,
            user,
        )

        return log

    def get_object_history(
        self, obj: Model, limit: int | None = None,
    ) -> list[Any]:
        """
        オブジェクトの変更履歴を取得する（django-simple-history）。

        Args:
            obj: 対象オブジェクト
            limit: 取得する履歴の最大数

        Returns:
            list: 履歴レコードのリスト

        Example:
            >>> service = AuditService()
            >>> history = service.get_object_history(my_object, limit=10)
            >>> for record in history:
            ...     print(f"{record.history_date}: {record.history_change_reason}")
        """
        if not hasattr(obj, "history"):
            logger.warning("Object %s does not have history tracking", obj)
            return []

        queryset = obj.history.all()

        if limit:
            queryset = queryset[:limit]

        return list(queryset)

    def get_object_audit_logs(
        self, obj: Model, limit: int | None = None,
    ) -> list[AuditLog]:
        """
        オブジェクトのカスタム監査ログを取得する。

        Args:
            obj: 対象オブジェクト
            limit: 取得するログの最大数

        Returns:
            list[AuditLog]: 監査ログのリスト

        Example:
            >>> service = AuditService()
            >>> logs = service.get_object_audit_logs(my_object)
            >>> for log in logs:
            ...     print(f"{log.event_name}: {log.description}")
        """
        queryset = AuditLog.objects.filter(
            model_name=obj._meta.model_name,
            object_id=str(obj.pk),
        )

        if limit:
            queryset = queryset[:limit]

        return list(queryset)

    def compare_history(self, obj: Model, version1_id: int, version2_id: int) -> dict:
        """
        2つの履歴バージョンを比較する。

        Args:
            obj: 対象オブジェクト
            version1_id: 比較元の履歴ID
            version2_id: 比較先の履歴ID

        Returns:
            dict: 変更されたフィールドと値の辞書

        Example:
            >>> service = AuditService()
            >>> diff = service.compare_history(obj, 1, 2)
            >>> print(diff)
            {'status': {'old': 'draft', 'new': 'submitted'}}
        """
        if not hasattr(obj, "history"):
            return {}

        try:
            version1 = obj.history.get(history_id=version1_id)
            version2 = obj.history.get(history_id=version2_id)
        except obj.history.model.DoesNotExist:
            logger.error("History version not found for object %s", obj)
            return {}

        changes = {}
        for field in obj._meta.fields:
            field_name = field.name
            old_value = getattr(version1, field_name, None)
            new_value = getattr(version2, field_name, None)

            if old_value != new_value:
                changes[field_name] = {
                    "old": old_value,
                    "new": new_value,
                }

        return changes

    def search_logs(
        self,
        user: "User | None" = None,
        event_type: str | None = None,
        model_name: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int | None = None,
    ) -> list[AuditLog]:
        """
        監査ログを検索する。

        Args:
            user: ユーザーでフィルタ
            event_type: イベントタイプでフィルタ
            model_name: モデル名でフィルタ
            start_date: 開始日時でフィルタ
            end_date: 終了日時でフィルタ
            limit: 取得する最大数

        Returns:
            list[AuditLog]: 検索結果のログリスト

        Example:
            >>> service = AuditService()
            >>> logs = service.search_logs(
            ...     event_type="approve",
            ...     start_date=datetime(2025, 1, 1),
            ...     limit=100
            ... )
        """
        queryset = AuditLog.objects.all()

        if user:
            queryset = queryset.filter(user=user)

        if event_type:
            queryset = queryset.filter(event_type=event_type)

        if model_name:
            queryset = queryset.filter(model_name=model_name)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        if limit:
            queryset = queryset[:limit]

        return list(queryset)

    def get_user_activity(
        self, user: "User", days: int = 30, limit: int | None = None,
    ) -> list[AuditLog]:
        """
        ユーザーの最近のアクティビティを取得する。

        Args:
            user: 対象ユーザー
            days: 過去何日分を取得するか
            limit: 取得する最大数

        Returns:
            list[AuditLog]: アクティビティログのリスト

        Example:
            >>> service = AuditService()
            >>> activity = service.get_user_activity(user, days=7)
            >>> print(f"User performed {len(activity)} actions in last 7 days")
        """
        start_date = timezone.now() - timezone.timedelta(days=days)

        return self.search_logs(
            user=user,
            start_date=start_date,
            limit=limit,
        )

    def generate_audit_report(
        self,
        obj: Model | None = None,
        user: "User | None" = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict:
        """
        監査レポートを生成する。

        Args:
            obj: 対象オブジェクト（省略可）
            user: 対象ユーザー（省略可）
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            dict: レポートデータ

        Example:
            >>> service = AuditService()
            >>> report = service.generate_audit_report(
            ...     start_date=datetime(2025, 1, 1),
            ...     end_date=datetime(2025, 1, 31)
            ... )
            >>> print(f"Total events: {report['total_events']}")
        """
        # クエリセット準備
        queryset = AuditLog.objects.all()

        if obj:
            queryset = queryset.filter(
                model_name=obj._meta.model_name,
                object_id=str(obj.pk),
            )

        if user:
            queryset = queryset.filter(user=user)

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)

        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

        # 統計情報収集
        total_events = queryset.count()

        event_type_counts = {}
        for event_type, _ in AuditLog.EVENT_TYPE_CHOICES:
            count = queryset.filter(event_type=event_type).count()
            if count > 0:
                event_type_counts[event_type] = count

        # ユーザー別アクティビティ
        user_activity = {}
        for log in queryset.values("user__email").distinct():
            email = log.get("user__email", "anonymous")
            if email:
                count = queryset.filter(user__email=email).count()
                user_activity[email] = count

        # モデル別変更数
        model_changes = {}
        for log in queryset.values("model_name").distinct():
            model_name = log["model_name"]
            count = queryset.filter(model_name=model_name).count()
            model_changes[model_name] = count

        return {
            "total_events": total_events,
            "event_type_counts": event_type_counts,
            "user_activity": user_activity,
            "model_changes": model_changes,
            "start_date": start_date,
            "end_date": end_date,
        }

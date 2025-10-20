"""DiaryEntryのビジネスロジック管理"""

from django.db import transaction

from school_diary.diary.models import ActionStatus
from school_diary.diary.models import DiaryEntry
from school_diary.diary.utils import get_current_classroom


class DiaryEntryService:
    """連絡帳エントリーの作成・更新サービス"""

    @staticmethod
    @transaction.atomic
    def create_entry(student, entry_date, **fields):
        """
        連絡帳エントリーを新規作成

        Args:
            student: 生徒ユーザー
            entry_date: 記載日
            **fields: その他のフィールド

        Returns:
            DiaryEntry: 作成されたエントリー

        Note:
            - classroom未指定時は自動設定
            - internal_actionがない場合、action_statusをNOT_REQUIREDに設定
        """
        # classroom自動設定（既存save()のline 203-206と同じロジック）
        if "classroom" not in fields:
            fields["classroom"] = get_current_classroom(student)

        # action_statusの初期化（既存save()のline 221-223と同じロジック）
        if "action_status" not in fields:
            internal_action = fields.get("internal_action")
            if not internal_action or internal_action == "":
                fields["action_status"] = ActionStatus.NOT_REQUIRED

        return DiaryEntry.objects.create(
            student=student,
            entry_date=entry_date,
            **fields,
        )

    @staticmethod
    @transaction.atomic
    def update_entry(entry, **fields):
        """
        連絡帳エントリーを更新

        Args:
            entry: DiaryEntryインスタンス
            **fields: 更新するフィールド

        Returns:
            DiaryEntry: 更新されたエントリー

        Note:
            - internal_action変更時、action_statusがCOMPLETEDの場合はリセット
        """
        # internal_action変更の検知（既存save()のline 209-216と同じロジック）
        if "internal_action" in fields:
            old_action = entry.internal_action
            new_action = fields["internal_action"]

            # internal_actionが変更され、対応済みの場合はリセット
            if old_action != new_action and entry.action_status == ActionStatus.COMPLETED:
                entry.action_status = ActionStatus.PENDING
                entry.action_completed_at = None
                entry.action_completed_by = None

        # フィールドを更新
        for key, value in fields.items():
            setattr(entry, key, value)

        entry.save()
        return entry

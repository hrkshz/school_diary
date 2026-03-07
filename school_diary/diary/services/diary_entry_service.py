"""DiaryEntryのビジネスロジック管理"""

from django.db import transaction
from django.utils import timezone

from school_diary.diary.models import ActionStatus
from school_diary.diary.models import DiaryEntry
from school_diary.diary.models import PublicReaction
from school_diary.diary.utils import get_current_classroom

UNSET = object()


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

    @staticmethod
    def _normalize_optional_value(value):
        """Normalize blank-like values to None while preserving UNSET."""
        if value is UNSET:
            return value
        if value in (None, ""):
            return None
        return value

    @classmethod
    def _reset_completion_metadata(cls, entry):
        """Reset completion metadata when an action is reopened or removed."""
        entry.action_completed_at = None
        entry.action_completed_by = None

    @classmethod
    def mark_read(
        cls,
        entry,
        teacher,
        reaction=UNSET,
        action=UNSET,
        action_status=UNSET,
    ):
        """Mark an entry as read and optionally update reaction/action state."""
        if not entry.is_read:
            entry.is_read = True
            entry.read_by = teacher
            entry.read_at = timezone.now()

        normalized_reaction = cls._normalize_optional_value(reaction)
        normalized_action = cls._normalize_optional_value(action)

        if normalized_reaction is not UNSET:
            entry.public_reaction = normalized_reaction

        if normalized_action is not UNSET:
            action_changed = entry.internal_action != normalized_action
            entry.internal_action = normalized_action

            if normalized_action is None:
                entry.action_status = ActionStatus.NOT_REQUIRED
                cls._reset_completion_metadata(entry)
            elif action_status is not UNSET:
                entry.action_status = action_status
                if action_status != ActionStatus.COMPLETED:
                    cls._reset_completion_metadata(entry)
            elif action_changed or entry.action_status == ActionStatus.NOT_REQUIRED:
                entry.action_status = ActionStatus.PENDING
                cls._reset_completion_metadata(entry)

        entry.save()
        return entry

    @classmethod
    def mark_as_read(cls, entry, teacher):
        """Backward-compatible existing read action."""
        return cls.mark_read(entry, teacher)

    @classmethod
    def mark_as_read_quick(cls, entry, teacher):
        """Mark as read with the default checked reaction."""
        return cls.mark_read(
            entry,
            teacher,
            reaction=PublicReaction.CHECKED,
            action=None,
        )

    @classmethod
    def create_action_task(cls, entry, teacher, internal_action):
        """Mark as read and create an in-progress teacher action task."""
        return cls.mark_read(
            entry,
            teacher,
            reaction=PublicReaction.CHECKED,
            action=internal_action,
            action_status=ActionStatus.IN_PROGRESS,
        )

    @staticmethod
    @transaction.atomic
    def save_attendance(*, attendance_model, student, classroom, date, status, noted_by, absence_reason=None):
        """Persist attendance for a student on a given day."""
        return attendance_model.objects.update_or_create(
            student=student,
            classroom=classroom,
            date=date,
            defaults={
                "status": status,
                "absence_reason": absence_reason,
                "noted_by": noted_by,
            },
        )

    @staticmethod
    def complete_action(entry, teacher, note=""):
        """対応完了処理"""
        entry.action_status = ActionStatus.COMPLETED
        entry.action_completed_at = timezone.now()
        entry.action_completed_by = teacher
        if note or note == "":
            entry.action_note = note or None
        entry.save()
        return entry

    @classmethod
    def mark_action_completed(cls, entry, teacher, note=""):
        """Backward-compatible completion action."""
        return cls.complete_action(entry, teacher, note=note)

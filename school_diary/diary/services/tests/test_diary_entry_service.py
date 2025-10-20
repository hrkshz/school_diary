"""DiaryEntryServiceのテスト"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from school_diary.diary.constants import ConditionLevel
from school_diary.diary.models import ActionStatus
from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DiaryEntry
from school_diary.diary.services.diary_entry_service import DiaryEntryService

User = get_user_model()


class TestDiaryEntryService(TestCase):
    """DiaryEntryServiceのテスト"""

    def setUp(self):
        """テストデータ準備"""
        # テストユーザー作成（生徒）
        self.student = User.objects.create_user(
            username="student1",
            email="student1@example.com",
        )
        # テストユーザー作成（教員）
        self.teacher = User.objects.create_user(
            username="teacher1",
            email="teacher1@example.com",
        )
        # テストクラス作成
        self.classroom = ClassRoom.objects.create(
            grade=1,
            class_name="A",
            academic_year=2025,
        )
        self.classroom.students.add(self.student)

    def test_create_entry_auto_sets_classroom(self):
        """連絡帳作成時にclassroomが自動設定される"""
        # Arrange & Act
        entry = DiaryEntryService.create_entry(
            student=self.student,
            entry_date="2025-10-19",
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト",
        )

        # Assert
        assert entry.classroom == self.classroom
        assert entry.student == self.student
        assert entry.reflection == "テスト"

    def test_create_entry_with_explicit_classroom(self):
        """classroom指定時にそれを尊重する"""
        # Arrange
        another_classroom = ClassRoom.objects.create(
            grade=2,
            class_name="B",
            academic_year=2025,
        )

        # Act
        entry = DiaryEntryService.create_entry(
            student=self.student,
            entry_date="2025-10-19",
            classroom=another_classroom,
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト",
        )

        # Assert
        assert entry.classroom == another_classroom

    def test_create_entry_initializes_action_status_not_required(self):
        """internal_actionがない場合、action_statusがNOT_REQUIREDに設定される"""
        # Arrange & Act
        entry = DiaryEntryService.create_entry(
            student=self.student,
            entry_date="2025-10-19",
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト",
            # internal_action未指定
        )

        # Assert
        assert entry.action_status == ActionStatus.NOT_REQUIRED

    def test_create_entry_with_internal_action_sets_pending(self):
        """internal_actionがある場合、action_statusがデフォルトのまま（models.pyのデフォルトはPENDING）"""
        # Arrange & Act
        entry = DiaryEntryService.create_entry(
            student=self.student,
            entry_date="2025-10-19",
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト",
            internal_action="needs_follow_up",
        )

        # Assert
        # action_statusは明示的に指定されていないため、models.pyのデフォルト値（PENDING）になる
        assert entry.internal_action == "needs_follow_up"
        assert entry.action_status == ActionStatus.PENDING

    def test_update_entry_changes_fields(self):
        """フィールドが正しく更新される"""
        # Arrange
        entry = DiaryEntry.objects.create(
            student=self.student,
            classroom=self.classroom,
            entry_date="2025-10-19",
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="最初のテキスト",
        )

        # Act
        updated_entry = DiaryEntryService.update_entry(
            entry,
            reflection="更新後のテキスト",
            health_condition=ConditionLevel.GOOD,
        )

        # Assert
        assert updated_entry.reflection == "更新後のテキスト"
        assert updated_entry.health_condition == ConditionLevel.GOOD

    def test_update_entry_resets_action_status_on_action_change(self):
        """internal_action変更時にaction_statusがリセットされる（COMPLETED→PENDING）"""
        # Arrange
        entry = DiaryEntry.objects.create(
            student=self.student,
            classroom=self.classroom,
            entry_date="2025-10-19",
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト",
            internal_action="needs_follow_up",
            action_status=ActionStatus.COMPLETED,
            action_completed_at=timezone.now(),
            action_completed_by=self.teacher,
        )

        # Act
        DiaryEntryService.update_entry(entry, internal_action="urgent")

        # Assert
        assert entry.internal_action == "urgent"
        assert entry.action_status == ActionStatus.PENDING
        assert entry.action_completed_at is None
        assert entry.action_completed_by is None

    def test_update_entry_no_reset_when_action_unchanged(self):
        """internal_action未変更時はaction_statusがリセットされない"""
        # Arrange
        entry = DiaryEntry.objects.create(
            student=self.student,
            classroom=self.classroom,
            entry_date="2025-10-19",
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト",
            internal_action="needs_follow_up",
            action_status=ActionStatus.COMPLETED,
            action_completed_at=timezone.now(),
            action_completed_by=self.teacher,
        )
        completed_at = entry.action_completed_at

        # Act
        DiaryEntryService.update_entry(entry, reflection="更新後")

        # Assert
        assert entry.action_status == ActionStatus.COMPLETED
        assert entry.action_completed_at == completed_at
        assert entry.action_completed_by == self.teacher

    def test_update_entry_no_reset_when_status_not_completed(self):
        """action_statusがCOMPLETED以外の場合はリセットされない"""
        # Arrange
        entry = DiaryEntry.objects.create(
            student=self.student,
            classroom=self.classroom,
            entry_date="2025-10-19",
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト",
            internal_action="needs_follow_up",
            action_status=ActionStatus.PENDING,
        )

        # Act
        DiaryEntryService.update_entry(entry, internal_action="urgent")

        # Assert
        assert entry.action_status == ActionStatus.PENDING  # そのまま
        assert entry.action_completed_at is None
        assert entry.action_completed_by is None

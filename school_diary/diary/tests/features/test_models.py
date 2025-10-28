"""
Models Unit Tests

このモジュールは内部ロジックの正確性をテストします（Unit Tests）。
統合テスト（Integration Tests）とは粒度が異なりますが、
両方を features/ ディレクトリで管理することで、保守性を向上させています。

テスト対象ビジネスロジック:
- DiaryEntry.clean(): action_status=COMPLETED時のバリデーション
- DiaryEntry.mark_as_read(): 既読処理
- DiaryEntry.mark_action_completed(): 対応完了処理
- DiaryEntry.is_editable: 編集可否判定
- ClassRoom.student_count: 生徒数カウント
- ClassRoom.is_teacher_of_class(): 担任判定
- UserProfile.clean(): ロール別バリデーション

Priority: P0（クリティカル）
"""

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from school_diary.diary.models import ActionStatus
from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DiaryEntry
from school_diary.diary.models import UserProfile


@pytest.mark.django_db
class TestDiaryEntryClean:
    """DiaryEntry.clean()のバリデーションテスト"""

    def test_clean_action_completed_without_completed_at_raises_error(
        self,
        student_user,
        yesterday,
    ):
        """
        Given: action_status=COMPLETED、action_completed_at=None
        When: clean()を呼ぶ
        Then: ValidationError発生
        """
        # Arrange
        entry = DiaryEntry(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            action_status=ActionStatus.COMPLETED,
            action_completed_at=None,
            action_completed_by=None,
        )

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            entry.clean()

        assert "action_completed_at" in exc_info.value.message_dict

    def test_clean_action_completed_without_completed_by_raises_error(
        self,
        student_user,
        teacher_user,
        yesterday,
    ):
        """
        Given: action_status=COMPLETED、action_completed_by=None
        When: clean()を呼ぶ
        Then: ValidationError発生
        """
        # Arrange
        entry = DiaryEntry(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            action_status=ActionStatus.COMPLETED,
            action_completed_at=timezone.now(),
            action_completed_by=None,
        )

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            entry.clean()

        assert "action_completed_by" in exc_info.value.message_dict

    def test_clean_action_completed_with_all_fields_success(
        self,
        student_user,
        teacher_user,
        yesterday,
    ):
        """
        Given: action_status=COMPLETED、全必須項目あり
        When: clean()を呼ぶ
        Then: エラーなし
        """
        # Arrange
        entry = DiaryEntry(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            action_status=ActionStatus.COMPLETED,
            action_completed_at=timezone.now(),
            action_completed_by=teacher_user,
        )

        # Act & Assert（例外が出ないことを確認）
        entry.clean()  # エラーが出なければ成功


@pytest.mark.django_db
class TestDiaryEntryMarkAsRead:
    """DiaryEntry.mark_as_read()のテスト"""

    def test_mark_as_read_updates_fields_correctly(
        self,
        diary_entry,
        teacher_user,
    ):
        """
        Given: 未読の連絡帳エントリー
        When: mark_as_read()を呼ぶ
        Then: is_read=True、read_by設定、read_at設定
        """
        # Arrange
        assert not diary_entry.is_read
        assert diary_entry.read_by is None
        assert diary_entry.read_at is None

        # Act
        diary_entry.mark_as_read(teacher_user)

        # Assert
        assert diary_entry.is_read
        assert diary_entry.read_by == teacher_user
        assert diary_entry.read_at is not None
        from datetime import datetime
        assert isinstance(diary_entry.read_at, datetime)


@pytest.mark.django_db
class TestDiaryEntryMarkActionCompleted:
    """DiaryEntry.mark_action_completed()のテスト"""

    def test_mark_action_completed_updates_fields_correctly(
        self,
        diary_entry,
        teacher_user,
    ):
        """
        Given: 連絡帳エントリー
        When: mark_action_completed()を呼ぶ
        Then: action_status=COMPLETED、action_completed_at設定、action_completed_by設定
        """
        # Arrange
        diary_entry.internal_action = "parent_contact"
        diary_entry.action_status = ActionStatus.IN_PROGRESS
        diary_entry.save()

        # Act
        diary_entry.mark_action_completed(teacher_user, note="保護者面談実施")

        # Assert
        assert diary_entry.action_status == ActionStatus.COMPLETED
        assert diary_entry.action_completed_at is not None
        assert diary_entry.action_completed_by == teacher_user
        assert diary_entry.action_note == "保護者面談実施"

    def test_mark_action_completed_without_note(
        self,
        diary_entry,
        teacher_user,
    ):
        """
        Given: 連絡帳エントリー
        When: mark_action_completed()をnoteなしで呼ぶ
        Then: action_status=COMPLETED、action_note変更なし（None or 既存値）
        """
        # Arrange
        diary_entry.internal_action = "parent_contact"
        diary_entry.action_status = ActionStatus.IN_PROGRESS
        diary_entry.save()

        # Act
        diary_entry.mark_action_completed(teacher_user)

        # Assert
        assert diary_entry.action_status == ActionStatus.COMPLETED
        assert diary_entry.action_note in (None, "")  # Models default: null=True


@pytest.mark.django_db
class TestDiaryEntryIsEditable:
    """DiaryEntry.is_editableプロパティのテスト"""

    def test_is_editable_returns_true_when_unread(self, diary_entry):
        """
        Given: 未読の連絡帳エントリー
        When: is_editableをチェック
        Then: True
        """
        # Arrange
        assert not diary_entry.is_read

        # Act & Assert
        assert diary_entry.is_editable

    def test_is_editable_returns_false_when_read(
        self,
        diary_entry,
        teacher_user,
    ):
        """
        Given: 既読の連絡帳エントリー
        When: is_editableをチェック
        Then: False
        """
        # Arrange
        diary_entry.mark_as_read(teacher_user)
        assert diary_entry.is_read

        # Act & Assert
        assert not diary_entry.is_editable


@pytest.mark.django_db
class TestClassRoomStudentCount:
    """ClassRoom.student_countプロパティのテスト"""

    def test_student_count_returns_correct_number(self, classroom, student_user):
        """
        Given: 生徒1名のクラス
        When: student_countをチェック
        Then: 1を返す
        """
        # Act
        count = classroom.student_count

        # Assert
        assert count == 1

    def test_student_count_returns_zero_when_no_students(self, db):
        """
        Given: 生徒0名のクラス
        When: student_countをチェック
        Then: 0を返す
        """
        # Arrange
        classroom = ClassRoom.objects.create(
            class_name="B",
            grade=2,
            academic_year=2025,
        )

        # Act
        count = classroom.student_count

        # Assert
        assert count == 0


@pytest.mark.django_db
class TestClassRoomIsTeacherOfClass:
    """ClassRoom.is_teacher_of_class()のテスト"""

    def test_is_teacher_of_class_returns_true_for_homeroom_teacher(
        self,
        classroom,
        teacher_user,
    ):
        """
        Given: 主担任のユーザー
        When: is_teacher_of_class()を呼ぶ
        Then: True
        """
        # Act
        result = classroom.is_teacher_of_class(teacher_user)

        # Assert
        assert result

    def test_is_teacher_of_class_returns_true_for_assistant_teacher(
        self,
        classroom,
    ):
        """
        Given: 副担任のユーザー
        When: is_teacher_of_class()を呼ぶ
        Then: True
        """
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        assistant = User.objects.create_user(
            username="assistant@test.com",
            email="assistant@test.com",
            password="testpass123",
        )
        classroom.assistant_teachers.add(assistant)

        # Act
        result = classroom.is_teacher_of_class(assistant)

        # Assert
        assert result

    def test_is_teacher_of_class_returns_false_for_non_teacher(
        self,
        classroom,
        student_user,
    ):
        """
        Given: 担任でないユーザー
        When: is_teacher_of_class()を呼ぶ
        Then: False
        """
        # Act
        result = classroom.is_teacher_of_class(student_user)

        # Assert
        assert not result


@pytest.mark.django_db
class TestUserProfileClean:
    """UserProfile.clean()のバリデーションテスト"""

    def test_clean_grade_leader_without_managed_grade_raises_error(
        self,
        db,
    ):
        """
        Given: role=grade_leader、managed_grade=None
        When: clean()を呼ぶ
        Then: ValidationError発生
        """
        # Arrange
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.create_user(
            username="leader@test.com",
            email="leader@test.com",
            password="testpass123",
        )
        profile = user.profile
        profile.role = UserProfile.ROLE_GRADE_LEADER
        profile.managed_grade = None

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            profile.clean()

        assert "managed_grade" in exc_info.value.message_dict

    def test_clean_grade_leader_with_managed_grade_success(
        self,
        grade_leader_user,
    ):
        """
        Given: role=grade_leader、managed_grade=1
        When: clean()を呼ぶ
        Then: エラーなし
        """
        # Act & Assert（例外が出ないことを確認）
        grade_leader_user.profile.clean()

    def test_clean_non_grade_leader_with_managed_grade_raises_error(
        self,
        student_user,
    ):
        """
        Given: role=student、managed_grade=1
        When: clean()を呼ぶ
        Then: ValidationError発生
        """
        # Arrange
        student_user.profile.managed_grade = 1

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            student_user.profile.clean()

        assert "managed_grade" in exc_info.value.message_dict

    def test_clean_student_without_managed_grade_success(
        self,
        student_user,
    ):
        """
        Given: role=student、managed_grade=None
        When: clean()を呼ぶ
        Then: エラーなし
        """
        # Arrange
        assert student_user.profile.role == UserProfile.ROLE_STUDENT
        assert student_user.profile.managed_grade is None

        # Act & Assert（例外が出ないことを確認）
        student_user.profile.clean()

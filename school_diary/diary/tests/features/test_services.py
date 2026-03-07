"""
Services Unit Tests

このモジュールは内部ロジックの正確性をテストします（Unit Tests）。
統合テスト（Integration Tests）とは粒度が異なりますが、
両方を features/ ディレクトリで管理することで、保守性を向上させています。

テスト対象サービスロジック:
- DiaryEntryService.create_entry(): classroom自動設定、action_status初期化
- DiaryEntryService.update_entry(): action_statusリセットロジック
- TeacherDashboardService.get_absence_data(): 欠席データ集計
- TeacherDashboardService.get_shared_notes(): 学年共有メモ取得

Priority: P0（クリティカル）
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from school_diary.diary.academic_year import get_current_academic_year
from school_diary.diary.authorization import can_access_student
from school_diary.diary.models import ActionStatus
from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DailyAttendance
from school_diary.diary.models import InternalAction
from school_diary.diary.models import PublicReaction
from school_diary.diary.models import TeacherNote
from school_diary.diary.models import UserProfile
from school_diary.diary.services.diary_entry_service import DiaryEntryService
from school_diary.diary.services.management_dashboard_service import ManagementDashboardService
from school_diary.diary.services.teacher_dashboard_service import TeacherDashboardService


@pytest.mark.django_db
class TestDiaryEntryServiceCreateEntry:
    """DiaryEntryService.create_entry()のテスト"""

    def test_create_entry_auto_sets_classroom(
        self,
        student_user,
        classroom,
        yesterday,
    ):
        """
        Given: classroomを指定しない
        When: create_entry()を呼ぶ
        Then: 自動的にclassroomが設定される
        """
        # Act
        entry = DiaryEntryService.create_entry(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
        )

        # Assert
        assert entry.classroom == classroom

    def test_create_entry_with_manual_classroom(
        self,
        student_user,
        yesterday,
    ):
        """
        Given: classroomを明示的に指定
        When: create_entry()を呼ぶ
        Then: 指定したclassroomが設定される
        """
        # Arrange
        other_classroom = ClassRoom.objects.create(
            class_name="B",
            grade=2,
            academic_year=get_current_academic_year(),
        )

        # Act
        entry = DiaryEntryService.create_entry(
            student=student_user,
            entry_date=yesterday,
            classroom=other_classroom,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
        )

        # Assert
        assert entry.classroom == other_classroom

    def test_create_entry_sets_action_status_not_required_when_no_internal_action(
        self,
        student_user,
        yesterday,
    ):
        """
        Given: internal_actionなし
        When: create_entry()を呼ぶ
        Then: action_status=NOT_REQUIRED
        """
        # Act
        entry = DiaryEntryService.create_entry(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
        )

        # Assert
        assert entry.action_status == ActionStatus.NOT_REQUIRED

    def test_create_entry_does_not_set_action_status_when_internal_action_provided(
        self,
        student_user,
        yesterday,
    ):
        """
        Given: internal_action設定
        When: create_entry()を呼ぶ
        Then: action_status=PENDING（デフォルト）
        """
        # Act
        entry = DiaryEntryService.create_entry(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            internal_action="parent_contact",
        )

        # Assert
        assert entry.action_status == ActionStatus.PENDING


@pytest.mark.django_db
class TestDiaryEntryServiceUpdateEntry:
    """DiaryEntryService.update_entry()のテスト"""

    def test_update_entry_resets_action_status_when_internal_action_changed(
        self,
        student_user,
        teacher_user,
        yesterday,
    ):
        """
        Given: action_status=COMPLETED、internal_action変更
        When: update_entry()を呼ぶ
        Then: action_status=PENDING、action_completed_at/byクリア
        """
        # Arrange
        entry = DiaryEntryService.create_entry(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            internal_action="parent_contact",
        )
        entry.mark_action_completed(teacher_user, note="対応完了")

        # Act
        updated_entry = DiaryEntryService.update_entry(
            entry,
            internal_action="individual_talk",  # 変更
        )

        # Assert
        assert updated_entry.action_status == ActionStatus.PENDING
        assert updated_entry.action_completed_at is None
        assert updated_entry.action_completed_by is None

    def test_update_entry_does_not_reset_action_status_when_no_change(
        self,
        student_user,
        teacher_user,
        yesterday,
    ):
        """
        Given: action_status=COMPLETED、internal_action変更なし
        When: update_entry()を呼ぶ
        Then: action_status=COMPLETED維持
        """
        # Arrange
        entry = DiaryEntryService.create_entry(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            internal_action="parent_contact",
        )
        entry.mark_action_completed(teacher_user, note="対応完了")

        # Act
        updated_entry = DiaryEntryService.update_entry(
            entry,
            reflection="更新",  # internal_action変更なし
        )

        # Assert
        assert updated_entry.action_status == ActionStatus.COMPLETED
        assert updated_entry.action_completed_by == teacher_user


@pytest.mark.django_db
class TestDiaryEntryServiceStateTransitions:
    """DiaryEntryServiceの状態遷移テスト"""

    def test_mark_read_updates_reaction_and_clears_action(self, student_user, teacher_user, yesterday):
        entry = DiaryEntryService.create_entry(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            internal_action=InternalAction.NEEDS_FOLLOW_UP,
        )

        DiaryEntryService.mark_read(
            entry,
            teacher_user,
            reaction=PublicReaction.CHECKED,
            action="",
        )

        assert entry.is_read is True
        assert entry.read_by == teacher_user
        assert entry.public_reaction == PublicReaction.CHECKED
        assert entry.internal_action is None
        assert entry.action_status == ActionStatus.NOT_REQUIRED

    def test_create_action_task_sets_in_progress(self, student_user, teacher_user, yesterday):
        entry = DiaryEntryService.create_entry(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
        )

        DiaryEntryService.create_action_task(entry, teacher_user, InternalAction.INDIVIDUAL_TALK)

        assert entry.is_read is True
        assert entry.public_reaction == PublicReaction.CHECKED
        assert entry.internal_action == InternalAction.INDIVIDUAL_TALK
        assert entry.action_status == ActionStatus.IN_PROGRESS

    def test_complete_action_sets_completion_metadata(self, student_user, teacher_user, yesterday):
        entry = DiaryEntryService.create_entry(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            internal_action=InternalAction.MONITORING,
        )

        DiaryEntryService.complete_action(entry, teacher_user, note="対応済み")

        assert entry.action_status == ActionStatus.COMPLETED
        assert entry.action_completed_by == teacher_user
        assert entry.action_note == "対応済み"


@pytest.mark.django_db
class TestTeacherDashboardServiceGetAbsenceData:
    """TeacherDashboardService.get_absence_data()のテスト"""

    def test_get_absence_data_returns_correct_counts(
        self,
        classroom,
        student_user,
        today,
    ):
        """
        Given: 欠席者2名（病気1名、家庭の都合1名）
        When: get_absence_data()を呼ぶ
        Then: 正しい集計結果を返す
        """
        # Arrange: 生徒2名追加
        from django.contrib.auth import get_user_model

        User = get_user_model()
        student2 = User.objects.create_user(
            username="student2@test.com",
            email="student2@test.com",
            password="testpass123",
        )
        classroom.students.add(student2)

        student3 = User.objects.create_user(
            username="student3@test.com",
            email="student3@test.com",
            password="testpass123",
        )
        classroom.students.add(student3)

        # 欠席記録作成
        DailyAttendance.objects.create(
            student=student2,
            classroom=classroom,
            date=today,
            status="absent",
            absence_reason="illness",
        )
        DailyAttendance.objects.create(
            student=student3,
            classroom=classroom,
            date=today,
            status="absent",
            absence_reason="family",
        )

        # Act
        result = TeacherDashboardService.get_absence_data(classroom, today)

        # Assert
        assert result["total_absent"] == 2
        assert result["absent_illness"] == 1
        assert len(result["absent_students"]) == 2

    def test_get_absence_data_with_no_absences(
        self,
        classroom,
        today,
    ):
        """
        Given: 欠席者なし
        When: get_absence_data()を呼ぶ
        Then: 0件を返す
        """
        # Act
        result = TeacherDashboardService.get_absence_data(classroom, today)

        # Assert
        assert result["total_absent"] == 0
        assert result["absent_illness"] == 0
        assert len(result["absent_students"]) == 0


@pytest.mark.django_db
class TestTeacherDashboardServiceGetSharedNotes:
    """TeacherDashboardService.get_shared_notes()のテスト"""

    def test_get_shared_notes_returns_same_grade_notes(
        self,
        classroom,
        teacher_user,
        student_user,
    ):
        """
        Given: 同じ学年の共有メモ
        When: get_shared_notes()を呼ぶ
        Then: 共有メモを取得
        """
        # Arrange: 別の担任作成
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_teacher = User.objects.create_user(
            username="other_teacher@test.com",
            email="other_teacher@test.com",
            password="testpass123",
        )
        other_teacher.profile.role = UserProfile.ROLE_TEACHER
        other_teacher.profile.save()

        # 共有メモ作成
        shared_note = TeacherNote.objects.create(
            teacher=other_teacher,
            student=student_user,
            note="学年共有メモ",
            is_shared=True,
        )

        # Act
        result = TeacherDashboardService.get_shared_notes(classroom, teacher_user)

        # Assert
        assert shared_note in result

    def test_get_shared_notes_excludes_own_notes(
        self,
        classroom,
        teacher_user,
        student_user,
    ):
        """
        Given: 自分が作成した共有メモ
        When: get_shared_notes()を呼ぶ
        Then: 除外される
        """
        # Arrange: 自分の共有メモ作成
        own_note = TeacherNote.objects.create(
            teacher=teacher_user,
            student=student_user,
            note="自分のメモ",
            is_shared=True,
        )

        # Act
        result = TeacherDashboardService.get_shared_notes(classroom, teacher_user)

        # Assert
        assert own_note not in result

    def test_get_shared_notes_excludes_non_shared_notes(
        self,
        classroom,
        teacher_user,
        student_user,
    ):
        """
        Given: 個人メモ（is_shared=False）
        When: get_shared_notes()を呼ぶ
        Then: 除外される
        """
        # Arrange: 別の担任の個人メモ作成
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_teacher = User.objects.create_user(
            username="other_teacher2@test.com",
            email="other_teacher2@test.com",
            password="testpass123",
        )
        other_teacher.profile.role = UserProfile.ROLE_TEACHER
        other_teacher.profile.save()

        private_note = TeacherNote.objects.create(
            teacher=other_teacher,
            student=student_user,
            note="個人メモ",
            is_shared=False,
        )

        # Act
        result = TeacherDashboardService.get_shared_notes(classroom, teacher_user)

        # Assert
        assert private_note not in result

    def test_get_shared_notes_excludes_old_notes(
        self,
        classroom,
        teacher_user,
        student_user,
    ):
        """
        Given: 古い共有メモ（14日以上前）
        When: get_shared_notes()を呼ぶ
        Then: 除外される
        """
        # Arrange: 古いメモ作成
        from django.contrib.auth import get_user_model

        from school_diary.diary.constants import NoteSettings

        User = get_user_model()
        other_teacher = User.objects.create_user(
            username="other_teacher3@test.com",
            email="other_teacher3@test.com",
            password="testpass123",
        )
        other_teacher.profile.role = UserProfile.ROLE_TEACHER
        other_teacher.profile.save()

        old_note = TeacherNote.objects.create(
            teacher=other_teacher,
            student=student_user,
            note="古いメモ",
            is_shared=True,
        )
        # 作成日時を過去に変更
        old_date = timezone.now() - timedelta(days=NoteSettings.SHARED_NOTE_DAYS + 1)
        TeacherNote.objects.filter(id=old_note.id).update(created_at=old_date)

        # Act
        result = TeacherDashboardService.get_shared_notes(classroom, teacher_user)

        # Assert
        assert old_note not in result


@pytest.mark.django_db
class TestManagementDashboardServiceAcademicYear:
    """管理ダッシュボードの年度選択テスト"""

    def test_grade_overview_uses_latest_academic_year(self):
        current_year = get_current_academic_year()
        old_classroom = ClassRoom.objects.create(class_name="A", grade=1, academic_year=current_year)
        latest_classroom = ClassRoom.objects.create(class_name="B", grade=1, academic_year=current_year + 1)

        result = ManagementDashboardService.get_grade_overview_data(managed_grade=1)

        classrooms = [item["classroom"] for item in result["classroom_stats"]]
        assert latest_classroom in classrooms
        assert old_classroom not in classrooms

    def test_school_overview_uses_latest_academic_year(self):
        current_year = get_current_academic_year()
        ClassRoom.objects.create(class_name="A", grade=1, academic_year=current_year)
        latest_classroom = ClassRoom.objects.create(class_name="B", grade=2, academic_year=current_year + 1)

        result = ManagementDashboardService.get_school_overview_data()

        grade_two = next(item for item in result["grade_stats"] if item["grade"] == 2)
        assert grade_two["class_count"] == 1
        assert latest_classroom.academic_year == current_year + 1


@pytest.mark.django_db
class TestAuthorizationHelpers:
    """認可ヘルパのテスト"""

    def test_assistant_teacher_can_access_student(self, classroom, student_user):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        assistant = User.objects.create_user(
            username="assistant_teacher@test.com",
            email="assistant_teacher@test.com",
            password="testpass123",
        )
        assistant.profile.role = UserProfile.ROLE_TEACHER
        assistant.profile.save()
        classroom.assistant_teachers.add(assistant)

        assert can_access_student(assistant, student_user) is True

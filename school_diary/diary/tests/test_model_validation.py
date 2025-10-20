"""
モデルバリデーションのテスト

H-MODEL-004: バリデーション不足の解消
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from school_diary.diary.models import AbsenceReason
from school_diary.diary.models import ActionStatus
from school_diary.diary.models import AttendanceStatus
from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DailyAttendance
from school_diary.diary.models import DiaryEntry
from school_diary.diary.models import UserProfile

User = get_user_model()


class TestDailyAttendanceValidation(TestCase):
    """DailyAttendanceのバリデーションテスト"""

    def setUp(self):
        """テストデータ準備"""
        self.student = User.objects.create_user(
            username="student1",
            email="student1@example.com",
        )
        self.teacher = User.objects.create_user(
            username="teacher1",
            email="teacher1@example.com",
        )
        self.classroom = ClassRoom.objects.create(
            grade=1,
            class_name="A",
            academic_year=2025,
        )

    def test_absent_without_reason_raises_error(self):
        """欠席時に理由なしでエラー"""
        attendance = DailyAttendance(
            student=self.student,
            classroom=self.classroom,
            date="2025-10-19",
            status=AttendanceStatus.ABSENT,
            absence_reason=None,
            noted_by=self.teacher,
        )

        with pytest.raises(ValidationError) as exc_info:
            attendance.full_clean()

        assert "absence_reason" in exc_info.value.error_dict

    def test_absent_with_reason_passes(self):
        """欠席時に理由ありで合格"""
        attendance = DailyAttendance(
            student=self.student,
            classroom=self.classroom,
            date="2025-10-19",
            status=AttendanceStatus.ABSENT,
            absence_reason=AbsenceReason.ILLNESS,
            noted_by=self.teacher,
        )

        # エラーが発生しないことを確認
        attendance.full_clean()

    def test_present_with_reason_raises_error(self):
        """出席時に理由ありでエラー"""
        attendance = DailyAttendance(
            student=self.student,
            classroom=self.classroom,
            date="2025-10-19",
            status=AttendanceStatus.PRESENT,
            absence_reason=AbsenceReason.ILLNESS,
            noted_by=self.teacher,
        )

        with pytest.raises(ValidationError) as exc_info:
            attendance.full_clean()

        assert "absence_reason" in exc_info.value.error_dict

    def test_present_without_reason_passes(self):
        """出席時に理由なしで合格"""
        attendance = DailyAttendance(
            student=self.student,
            classroom=self.classroom,
            date="2025-10-19",
            status=AttendanceStatus.PRESENT,
            absence_reason=None,
            noted_by=self.teacher,
        )

        # エラーが発生しないことを確認
        attendance.full_clean()


class TestUserProfileValidation(TestCase):
    """UserProfileのバリデーションテスト"""

    def setUp(self):
        """テストデータ準備"""
        self.user = User.objects.create_user(
            username="grade_leader1",
            email="grade_leader1@example.com",
        )
        # signals.pyで自動作成されたUserProfileを取得
        self.profile = UserProfile.objects.get(user=self.user)

    def test_grade_leader_without_managed_grade_raises_error(self):
        """学年主任時に管理学年なしでエラー"""
        self.profile.role = "grade_leader"
        self.profile.managed_grade = None

        with pytest.raises(ValidationError) as exc_info:
            self.profile.full_clean()

        assert "managed_grade" in exc_info.value.error_dict

    def test_grade_leader_with_managed_grade_passes(self):
        """学年主任時に管理学年ありで合格"""
        self.profile.role = "grade_leader"
        self.profile.managed_grade = 1

        # エラーが発生しないことを確認
        self.profile.full_clean()

    def test_teacher_with_managed_grade_raises_error(self):
        """担任時に管理学年ありでエラー"""
        self.profile.role = "teacher"
        self.profile.managed_grade = 1

        with pytest.raises(ValidationError) as exc_info:
            self.profile.full_clean()

        assert "managed_grade" in exc_info.value.error_dict

    def test_teacher_without_managed_grade_passes(self):
        """担任時に管理学年なしで合格"""
        self.profile.role = "teacher"
        self.profile.managed_grade = None

        # エラーが発生しないことを確認
        self.profile.full_clean()


class TestDiaryEntryValidation(TestCase):
    """DiaryEntryのバリデーションテスト"""

    def setUp(self):
        """テストデータ準備"""
        self.student = User.objects.create_user(
            username="student1",
            email="student1@example.com",
        )
        self.teacher = User.objects.create_user(
            username="teacher1",
            email="teacher1@example.com",
        )
        self.classroom = ClassRoom.objects.create(
            grade=1,
            class_name="A",
            academic_year=2025,
        )

    def test_completed_without_completed_at_raises_error(self):
        """対応完了時に対応完了日時なしでエラー"""
        entry = DiaryEntry(
            student=self.student,
            classroom=self.classroom,
            entry_date="2025-10-19",
            health_condition=3,
            mental_condition=3,
            reflection="テスト",
            action_status=ActionStatus.COMPLETED,
            action_completed_at=None,
            action_completed_by=self.teacher,
        )

        with pytest.raises(ValidationError) as exc_info:
            entry.full_clean()

        assert "action_completed_at" in exc_info.value.error_dict

    def test_completed_without_completed_by_raises_error(self):
        """対応完了時に対応者なしでエラー"""
        entry = DiaryEntry(
            student=self.student,
            classroom=self.classroom,
            entry_date="2025-10-19",
            health_condition=3,
            mental_condition=3,
            reflection="テスト",
            action_status=ActionStatus.COMPLETED,
            action_completed_at=timezone.now(),
            action_completed_by=None,
        )

        with pytest.raises(ValidationError) as exc_info:
            entry.full_clean()

        assert "action_completed_by" in exc_info.value.error_dict

    def test_completed_with_all_fields_passes(self):
        """対応完了時に全フィールドありで合格"""
        entry = DiaryEntry(
            student=self.student,
            classroom=self.classroom,
            entry_date="2025-10-19",
            health_condition=3,
            mental_condition=3,
            reflection="テスト",
            action_status=ActionStatus.COMPLETED,
            action_completed_at=timezone.now(),
            action_completed_by=self.teacher,
        )

        # エラーが発生しないことを確認
        entry.full_clean()

    def test_pending_without_completed_fields_passes(self):
        """対応中時に対応完了フィールドなしで合格"""
        entry = DiaryEntry(
            student=self.student,
            classroom=self.classroom,
            entry_date="2025-10-19",
            health_condition=3,
            mental_condition=3,
            reflection="テスト",
            action_status=ActionStatus.PENDING,
            action_completed_at=None,
            action_completed_by=None,
        )

        # エラーが発生しないことを確認
        entry.full_clean()

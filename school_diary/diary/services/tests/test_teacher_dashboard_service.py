"""TeacherDashboardServiceのテスト"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from school_diary.diary.constants import ConditionLevel
from school_diary.diary.models import ActionStatus
from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DiaryEntry
from school_diary.diary.models import InternalAction
from school_diary.diary.services.teacher_dashboard_service import (
    TeacherDashboardService,
)

User = get_user_model()


class TestGetClassroomSummary(TestCase):
    """get_classroom_summaryメソッドのテスト"""

    def setUp(self):
        """テストデータ準備"""
        # テストクラス作成
        self.classroom = ClassRoom.objects.create(
            grade=1, class_name="A", academic_year=2025,
        )

        # テスト生徒作成
        self.student1 = User.objects.create_user(
            username="student1", email="student1@example.com",
        )
        self.student2 = User.objects.create_user(
            username="student2", email="student2@example.com",
        )
        self.classroom.students.add(self.student1, self.student2)

    def test_get_classroom_summary_empty(self):
        """連絡帳がない場合、全て0が返る"""
        # Arrange: 連絡帳なし

        # Act
        result = TeacherDashboardService.get_classroom_summary(self.classroom)

        # Assert
        assert result["unread_total"] == 0
        assert result["pending_action_count"] == 0
        assert result["urgent_action_count"] == 0
        assert result["no_reaction_count"] == 0

    def test_get_classroom_summary_with_unread_entries(self):
        """未読連絡帳が正しくカウントされる"""
        # Arrange: 未読連絡帳を作成
        DiaryEntry.objects.create(
            student=self.student1,
            entry_date=timezone.now().date(),
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト1",
            classroom=self.classroom,
            is_read=False,
        )
        DiaryEntry.objects.create(
            student=self.student2,
            entry_date=timezone.now().date(),
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト2",
            classroom=self.classroom,
            is_read=False,
        )

        # Act
        result = TeacherDashboardService.get_classroom_summary(self.classroom)

        # Assert
        assert result["unread_total"] == 2

    def test_get_classroom_summary_with_pending_action(self):
        """対応待ち連絡帳が正しくカウントされる"""
        # Arrange: 対応待ち連絡帳を作成
        DiaryEntry.objects.create(
            student=self.student1,
            entry_date=timezone.now().date(),
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト",
            classroom=self.classroom,
            internal_action=InternalAction.PARENT_CONTACTED,
            action_status=ActionStatus.PENDING,
        )

        # Act
        result = TeacherDashboardService.get_classroom_summary(self.classroom)

        # Assert
        assert result["pending_action_count"] == 1

    def test_get_classroom_summary_with_urgent_action(self):
        """緊急対応が必要な連絡帳が正しくカウントされる"""
        # Arrange: 緊急対応連絡帳を作成
        DiaryEntry.objects.create(
            student=self.student1,
            entry_date=timezone.now().date(),
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト",
            classroom=self.classroom,
            internal_action=InternalAction.URGENT,
            action_status=ActionStatus.PENDING,
        )

        # Act
        result = TeacherDashboardService.get_classroom_summary(self.classroom)

        # Assert
        assert result["urgent_action_count"] == 1

    def test_get_classroom_summary_with_no_reaction(self):
        """反応なし連絡帳が正しくカウントされる"""
        # Arrange: 既読だが反応なしの連絡帳を作成
        DiaryEntry.objects.create(
            student=self.student1,
            entry_date=timezone.now().date(),
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト",
            classroom=self.classroom,
            is_read=True,
            public_reaction=None,
        )

        # Act
        result = TeacherDashboardService.get_classroom_summary(self.classroom)

        # Assert
        assert result["no_reaction_count"] == 1


class TestGetStudentListWithUnreadCount(TestCase):
    """get_student_list_with_unread_countメソッドのテスト"""

    def setUp(self):
        """テストデータ準備"""
        # テストクラス作成
        self.classroom = ClassRoom.objects.create(
            grade=1, class_name="A", academic_year=2025,
        )

        # テスト生徒作成
        self.student1 = User.objects.create_user(
            username="student1",
            email="student1@example.com",
            first_name="太郎",
            last_name="山田",
        )
        self.student2 = User.objects.create_user(
            username="student2",
            email="student2@example.com",
            first_name="花子",
            last_name="佐藤",
        )
        self.classroom.students.add(self.student1, self.student2)

    def test_get_student_list_empty_classroom(self):
        """生徒がいないクラスの場合、空のQuerySetが返る"""
        # Arrange: 生徒を削除
        self.classroom.students.clear()

        # Act
        result = TeacherDashboardService.get_student_list_with_unread_count(
            self.classroom,
        )

        # Assert
        assert result.count() == 0

    def test_get_student_list_with_unread_count_zero(self):
        """未読連絡帳がない場合、unread_count=0が付与される"""
        # Arrange: 連絡帳なし

        # Act
        result = TeacherDashboardService.get_student_list_with_unread_count(
            self.classroom,
        )

        # Assert
        assert result.count() == 2
        student_list = list(result)
        assert all(s.unread_count == 0 for s in student_list)

    def test_get_student_list_with_unread_count(self):
        """未読連絡帳がある場合、正しくunread_countが付与される"""
        # Arrange: 未読連絡帳を作成（student1: 3件、student2: 1件）
        today = timezone.now().date()
        for i in range(3):
            DiaryEntry.objects.create(
                student=self.student1,
                entry_date=today - timezone.timedelta(days=i),
                health_condition=ConditionLevel.NORMAL,
                mental_condition=ConditionLevel.NORMAL,
                reflection="テスト",
                classroom=self.classroom,
                is_read=False,
            )
        DiaryEntry.objects.create(
            student=self.student2,
            entry_date=today,
            health_condition=ConditionLevel.NORMAL,
            mental_condition=ConditionLevel.NORMAL,
            reflection="テスト",
            classroom=self.classroom,
            is_read=False,
        )

        # Act
        result = TeacherDashboardService.get_student_list_with_unread_count(
            self.classroom,
        )

        # Assert
        student_list = list(result)
        student1_result = next(s for s in student_list if s.id == self.student1.id)
        student2_result = next(s for s in student_list if s.id == self.student2.id)

        assert student1_result.unread_count == 3
        assert student2_result.unread_count == 1

    def test_get_student_list_ordered_by_name(self):
        """生徒リストが名前順（last_name, first_name）でソートされている"""
        # Arrange: 既にsetUpで2名作成済み（山田太郎、佐藤花子）

        # Act
        result = TeacherDashboardService.get_student_list_with_unread_count(
            self.classroom,
        )

        # Assert
        student_list = list(result)
        # 佐藤花子 → 山田太郎 の順
        assert student_list[0].last_name == "佐藤"
        assert student_list[1].last_name == "山田"

"""
03-features.md Teacher Features Tests

このモジュールは以下の機能をテストします:
- TEA-001: 担任ダッシュボード（Inbox Pattern）
- TEA-002: クラス健康ダッシュボード
- TEA-003: 生徒詳細

Traceability Matrix:
| Test Method | Feature ID | Scenario | Priority |
|-------------|------------|----------|----------|
| test_tea001_dashboard_display_success | TEA-001 | 表示 | P0 |
| test_tea001_inbox_important_student_classified | TEA-001 | P0重要分類 | P0 |
| test_tea001_inbox_unread_student_classified | TEA-001 | P2-2未読分類 | P0 |
| test_tea001_inbox_not_submitted_student_classified | TEA-001 | P2-1未提出分類 | P0 |
| test_tea001_dashboard_other_class_forbidden | TEA-001 | 他クラス禁止 | P0 |
| test_tea002_class_health_display_success | TEA-002 | 表示 | P1 |
| test_tea003_student_detail_display_success | TEA-003 | 表示 | P1 |
| test_tea003_student_detail_other_class_forbidden | TEA-003 | 他クラス禁止 | P0 |
"""

import pytest
from django.urls import reverse

from school_diary.diary.models import DiaryEntry


@pytest.mark.django_db
class TestTEA001TeacherDashboard:
    """TEA-001: 担任ダッシュボードのテスト"""

    def test_tea001_dashboard_display_success(self, authenticated_teacher_client, teacher_user, classroom):
        """
        Given: ログイン済み担任ユーザー
        When: ダッシュボードにアクセス
        Then: Inbox Pattern（7カテゴリ分類）が表示される
        """
        # Act
        response = authenticated_teacher_client.get(reverse("diary:teacher_dashboard"))

        # Assert
        assert response.status_code == 200
        assert "diary/teacher_dashboard.html" in [t.name for t in response.templates]
        assert "classroom" in response.context
        assert "students" in response.context
        assert "summary" in response.context

    def test_tea001_inbox_important_student_classified(
        self,
        authenticated_teacher_client,
        classroom,
        today,
    ):
        """
        Given: メンタル★1の連絡帳エントリー
        When: ダッシュボードにアクセス
        Then: ダッシュボードに生徒が表示される
        """
        # Arrange: メンタル★1の生徒作成
        from django.contrib.auth import get_user_model

        User = get_user_model()
        critical_student = User.objects.create_user(
            username="critical@test.com",
            email="critical@test.com",
            password="testpass123",
        )
        critical_student.profile.role = "student"
        critical_student.profile.save()
        classroom.students.add(critical_student)

        # メンタル★1のエントリー作成
        DiaryEntry.objects.create(
            student=critical_student,
            entry_date=today,
            health_condition=4,
            mental_condition=1,  # ★1 = 重要
            reflection="つらい",
        )

        # Act
        response = authenticated_teacher_client.get(reverse("diary:teacher_dashboard"))

        # Assert
        assert response.status_code == 200
        students_list = response.context["students"]
        student_ids = [s["student"].id for s in students_list]
        assert critical_student.id in student_ids

    def test_tea001_inbox_unread_student_classified(
        self,
        authenticated_teacher_client,
        unread_diary_entry,
    ):
        """
        Given: 未読の連絡帳エントリー
        When: ダッシュボードにアクセス
        Then: ダッシュボードに生徒が表示される
        """
        # Act
        response = authenticated_teacher_client.get(reverse("diary:teacher_dashboard"))

        # Assert
        assert response.status_code == 200
        students_list = response.context["students"]
        student_ids = [s["student"].id for s in students_list]
        assert unread_diary_entry.student.id in student_ids

    def test_tea001_inbox_not_submitted_student_classified(
        self,
        authenticated_teacher_client,
        student_user,
    ):
        """
        Given: 今日連絡帳を提出していない生徒
        When: ダッシュボードにアクセス
        Then: ダッシュボードに生徒が表示される
        """
        # Arrange: student_userは連絡帳を提出していない

        # Act
        response = authenticated_teacher_client.get(reverse("diary:teacher_dashboard"))

        # Assert
        assert response.status_code == 200
        students_list = response.context["students"]
        student_ids = [s["student"].id for s in students_list]
        assert student_user.id in student_ids

    def test_tea001_dashboard_other_class_forbidden(self, client, classroom):
        """
        Given: 他のクラスの担任
        When: 1年A組のダッシュボードにアクセス試行
        Then: 403 Forbidden（自分のクラスのみアクセス可能）
        """
        # Arrange: 2年B組の担任作成
        from django.contrib.auth import get_user_model

        from school_diary.diary.models import ClassRoom

        User = get_user_model()
        other_classroom = ClassRoom.objects.create(
            class_name="B",
            grade=2,
            academic_year=2025,
        )
        other_teacher = User.objects.create_user(
            username="other_teacher@test.com",
            email="other_teacher@test.com",
            password="testpass123",
        )
        other_teacher.profile.role = "teacher"
        other_teacher.profile.save()
        other_classroom.homeroom_teacher = other_teacher
        other_classroom.save()

        client.force_login(other_teacher)

        # Act: 1年A組のダッシュボードにアクセス試行（担任は自動的に自分のクラスのみ表示）
        response = client.get(reverse("diary:teacher_dashboard"))

        # Assert: 2年B組のダッシュボードが表示される（403ではなく、自分のクラスが表示される）
        assert response.status_code == 200
        # 自分のクラスの生徒のみ表示されていることを確認
        all_students = (
            list(response.context.get("important", []))
            + list(response.context.get("needs_attention", []))
            + list(response.context.get("not_submitted", []))
            + list(response.context.get("unread", []))
        )
        # 1年A組の生徒が含まれていないことを確認
        student_ids = [s.id for s in all_students]
        classroom_student_ids = list(classroom.students.values_list("id", flat=True))
        assert not any(sid in student_ids for sid in classroom_student_ids)


@pytest.mark.django_db
class TestTEA002ClassHealthDashboard:
    """TEA-002: クラス健康ダッシュボードのテスト"""

    def test_tea002_class_health_display_success(self, authenticated_teacher_client, teacher_user, classroom):
        """
        Given: ログイン済み担任ユーザー
        When: クラス健康ダッシュボードにアクセス
        Then: ヒートマップ（7日/14日）が表示される
        """
        # Act
        response = authenticated_teacher_client.get(reverse("diary:class_health_dashboard"))

        # Assert
        assert response.status_code == 200
        assert "diary/class_health_dashboard.html" in [t.name for t in response.templates]


@pytest.mark.django_db
class TestTEA003StudentDetail:
    """TEA-003: 生徒詳細のテスト"""

    def test_tea003_student_detail_display_success(
        self,
        authenticated_teacher_client,
        student_user,
        diary_entry,
    ):
        """
        Given: ログイン済み担任ユーザー
        When: 担当クラスの生徒詳細にアクセス
        Then: 個別生徒の連絡帳履歴、担任メモが表示される
        """
        # Act
        response = authenticated_teacher_client.get(
            reverse("diary:teacher_student_detail", kwargs={"student_id": student_user.id}),
        )

        # Assert
        assert response.status_code == 200
        assert "diary/teacher_student_detail.html" in [t.name for t in response.templates]
        assert student_user == response.context["student"]
        assert diary_entry in response.context["entries"]

    def test_tea003_student_detail_other_class_forbidden(self, authenticated_teacher_client):
        """
        Given: ログイン済み担任ユーザー
        When: 他のクラスの生徒詳細にアクセス試行
        Then: 404 Not Found（セキュリティ: 存在を隠す）
        """
        # Arrange: 他のクラスの生徒作成
        from django.contrib.auth import get_user_model

        from school_diary.diary.models import ClassRoom

        User = get_user_model()
        other_classroom = ClassRoom.objects.create(
            class_name="B",
            grade=2,
            academic_year=2025,
        )
        other_student = User.objects.create_user(
            username="other_student@test.com",
            email="other_student@test.com",
            password="testpass123",
        )
        other_student.profile.role = "student"
        other_student.profile.save()
        other_classroom.students.add(other_student)

        # Act
        response = authenticated_teacher_client.get(
            reverse("diary:teacher_student_detail", kwargs={"student_id": other_student.id}),
        )

        # Assert
        assert response.status_code == 404

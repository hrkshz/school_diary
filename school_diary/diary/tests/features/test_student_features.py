"""
03-features.md Student Features Tests

このモジュールは以下の機能をテストします:
- STU-001: 生徒ダッシュボード
- STU-002: 連絡帳作成
- STU-003: 連絡帳編集
- STU-004: 連絡帳履歴

Traceability Matrix:
| Test Method | Feature ID | Scenario | Priority |
|-------------|------------|----------|----------|
| test_stu001_dashboard_display_success | STU-001 | 表示 | P0 |
| test_stu002_create_valid_entry_success | STU-002 | 正常系 | P0 |
| test_stu002_create_duplicate_date_rejected | STU-002 | 一日一件制約 | P0 |
| test_stu002_create_missing_required_field_rejected | STU-002 | 必須項目 | P1 |
| test_stu003_edit_before_read_success | STU-003 | 既読前 | P0 |
| test_stu003_edit_after_read_rejected | STU-003 | 既読後 | P0 |
| test_stu003_edit_other_student_entry_forbidden | STU-003 | 他生徒 | P0 |
| test_stu004_history_display_success | STU-004 | 表示 | P1 |
"""

import pytest
from django.urls import reverse

from school_diary.diary.models import DiaryEntry


@pytest.mark.django_db
class TestSTU001StudentDashboard:
    """STU-001: 生徒ダッシュボードのテスト"""

    def test_stu001_dashboard_display_success(self, authenticated_student_client, student_user, diary_entry):
        """
        Given: ログイン済み生徒ユーザー
        When: ダッシュボードにアクセス
        Then: 過去7日分の連絡帳が表示される
        """
        # Act
        response = authenticated_student_client.get(reverse("diary:student_dashboard"))

        # Assert
        assert response.status_code == 200
        assert "diary/student_dashboard.html" in [t.name for t in response.templates]
        assert diary_entry in response.context["entries"]


@pytest.mark.django_db
class TestSTU002DiaryCreation:
    """STU-002: 連絡帳作成機能のテスト"""

    def test_stu002_create_valid_entry_success(self, authenticated_student_client, student_user, today):
        """
        Given: ログイン済み生徒ユーザー
        When: 有効な連絡帳データを送信
        Then: 連絡帳が作成され、ダッシュボードにリダイレクト
        """
        # Arrange
        data = {
            "health_condition": 4,
            "mental_condition": 4,
            "reflection": "今日は楽しかった",
        }

        # Act
        response = authenticated_student_client.post(reverse("diary:create"), data)

        # Assert
        assert response.status_code == 302
        assert response.url == reverse("diary:student_dashboard")

        # 連絡帳が作成されたことを確認
        entry = DiaryEntry.objects.get(student=student_user, entry_date=today)
        assert entry.health_condition == 4
        assert entry.mental_condition == 4
        assert entry.reflection == "今日は楽しかった"

    def test_stu002_create_duplicate_date_rejected(self, authenticated_student_client, student_user, diary_entry):
        """
        Given: 既に今日の連絡帳が存在する
        When: 同じ日付で連絡帳作成を試行
        Then: エラーメッセージが表示され、作成失敗
        """
        # Arrange
        data = {
            "health_condition": 4,
            "mental_condition": 4,
            "reflection": "2件目の連絡帳",
        }

        # Act
        response = authenticated_student_client.post(
            reverse("diary:create"),
            data,
        )

        # Assert
        assert response.status_code == 200  # フォーム再表示
        assert "既に連絡帳が存在します" in response.content.decode()

    def test_stu002_create_missing_required_field_rejected(self, authenticated_student_client):
        """
        Given: ログイン済み生徒ユーザー
        When: 必須項目（reflection）なしで送信
        Then: バリデーションエラーが表示される
        """
        # Arrange
        data = {
            "health_condition": 4,
            "mental_condition": 4,
            # reflection なし
        }

        # Act
        response = authenticated_student_client.post(reverse("diary:create"), data)

        # Assert
        assert response.status_code == 200  # フォーム再表示
        assert "必須" in response.content.decode() or "required" in response.content.decode().lower()


@pytest.mark.django_db
class TestSTU003DiaryEditing:
    """STU-003: 連絡帳編集機能のテスト"""

    def test_stu003_edit_before_read_success(self, authenticated_student_client, student_user, diary_entry):
        """
        Given: 既読前の連絡帳エントリー
        When: 編集を試行
        Then: 編集成功
        """
        # Arrange
        assert not diary_entry.is_read  # 既読前であることを確認

        data = {
            "health_condition": 3,
            "mental_condition": 3,
            "reflection": "修正しました",
        }

        # Act
        response = authenticated_student_client.post(
            reverse("diary:edit", kwargs={"pk": diary_entry.pk}),
            data,
        )

        # Assert
        assert response.status_code == 302
        diary_entry.refresh_from_db()
        assert diary_entry.reflection == "修正しました"

    def test_stu003_edit_after_read_rejected(self, authenticated_student_client, student_user, diary_entry):
        """
        Given: 既読後の連絡帳エントリー
        When: 編集を試行
        Then: 403 Forbidden
        """
        # Arrange
        diary_entry.is_read = True
        diary_entry.save()

        # Act
        response = authenticated_student_client.get(reverse("diary:edit", kwargs={"pk": diary_entry.pk}))

        # Assert
        assert response.status_code == 403

    def test_stu003_edit_other_student_entry_forbidden(self, client, classroom):
        """
        Given: 他の生徒の連絡帳エントリー
        When: 編集を試行
        Then: 403 Forbidden
        """
        # Arrange: 生徒A作成
        from django.contrib.auth import get_user_model

        User = get_user_model()
        student_a = User.objects.create_user(
            username="student_a@test.com",
            email="student_a@test.com",
            password="testpass123",
        )
        student_a.profile.role = "student"
        student_a.profile.save()
        classroom.students.add(student_a)

        # 生徒Aの連絡帳作成
        entry_a = DiaryEntry.objects.create(
            student=student_a,
            entry_date="2025-10-23",
            health_condition=4,
            mental_condition=4,
            reflection="生徒Aの連絡帳",
        )

        # 生徒B作成
        student_b = User.objects.create_user(
            username="student_b@test.com",
            email="student_b@test.com",
            password="testpass123",
        )
        student_b.profile.role = "student"
        student_b.profile.save()
        classroom.students.add(student_b)

        client.force_login(student_b)

        # Act: 生徒Bが生徒Aの連絡帳を編集試行
        response = client.get(reverse("diary:edit", kwargs={"pk": entry_a.pk}))

        # Assert
        assert response.status_code == 403


@pytest.mark.django_db
class TestSTU004DiaryHistory:
    """STU-004: 連絡帳履歴のテスト"""

    def test_stu004_history_display_success(self, authenticated_student_client, student_user, diary_entry):
        """
        Given: ログイン済み生徒ユーザー
        When: 履歴ページにアクセス
        Then: 過去の連絡帳一覧が表示される
        """
        # Act
        response = authenticated_student_client.get(reverse("diary:history"))

        # Assert
        assert response.status_code == 200
        assert "diary/history.html" in [t.name for t in response.templates]
        assert diary_entry in response.context["entries"]

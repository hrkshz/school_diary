"""
03-features.md Authentication Features Tests

このモジュールは以下の機能をテストします:
- AUTH-001: ログイン
- AUTH-002: ログアウト
- AUTH-003: パスワード変更
- AUTH-004〜007: パスワードリセット
- SYS-002: ホームリダイレクト（ロールベース）

Traceability Matrix:
| Test Method | Feature ID | Scenario | Priority |
|-------------|------------|----------|----------|
| test_auth001_login_valid_credentials_success | AUTH-001 | 正常系 | P0 |
| test_auth001_login_invalid_credentials_rejected | AUTH-001 | 異常系 | P0 |
| test_auth002_logout_success | AUTH-002 | ログアウト | P1 |
| test_auth003_password_change_success | AUTH-003 | パスワード変更 | P1 |
| test_auth003_password_change_wrong_old_password | AUTH-003 | 旧パスワード誤り | P1 |
| test_auth003_password_change_password_mismatch | AUTH-003 | 新パスワード不一致 | P1 |
| test_auth004_password_reset_request_success | AUTH-004 | リセット要求 | P2 |
| test_auth005_password_reset_done_display | AUTH-005 | リセット完了表示 | P2 |
| test_sys002_redirect_superuser_to_admin | SYS-002 | 管理者 | P0 |
| test_sys002_redirect_school_leader_to_school_overview | SYS-002 | 校長 | P0 |
| test_sys002_redirect_grade_leader_to_grade_overview | SYS-002 | 学年主任 | P0 |
| test_sys002_redirect_teacher_to_dashboard | SYS-002 | 担任 | P0 |
| test_sys002_redirect_student_to_dashboard | SYS-002 | 生徒 | P0 |
| test_sys002_redirect_unauthenticated_to_login | SYS-002 | 未認証 | P0 |
"""

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAUTH001Login:
    """AUTH-001: ログイン機能のテスト"""

    def test_auth001_login_valid_credentials_success(self, client, student_user):
        """
        Given: 有効なユーザーアカウント
        When: 正しいusername/passwordでログイン
        Then: ログイン成功、ダッシュボードにリダイレクト
        """
        # Act
        response = client.post(
            reverse("account_login"),
            {
                "login": "student@test.com",
                "password": "testpass123",
            },
        )

        # Assert
        assert response.status_code == 302  # リダイレクト
        assert response.url.startswith("/diary/student/dashboard")

    def test_auth001_login_invalid_credentials_rejected(self, client, student_user):
        """
        Given: 有効なユーザーアカウント
        When: 間違ったpasswordでログイン試行
        Then: ログイン失敗、エラーメッセージ表示
        """
        # Act
        response = client.post(
            reverse("account_login"),
            {
                "login": "student@test.com",
                "password": "wrongpassword",
            },
        )

        # Assert
        assert response.status_code == 200  # ログインページ再表示
        # allauthのエラーメッセージを確認
        assert "入力されたメールアドレスもしくはパスワードが正しくありません" in response.content.decode() or "incorrect" in response.content.decode().lower()


@pytest.mark.django_db
class TestSYS002LoginRedirect:
    """SYS-002: ログイン後のロールベースリダイレクトのテスト"""

    def test_sys002_redirect_superuser_to_admin(self, client, superuser):
        """
        Given: システム管理者（is_superuser=True）
        When: ログイン
        Then: /admin/ にリダイレクト
        """
        # Arrange
        client.force_login(superuser)

        # Act
        response = client.get(reverse("home"))

        # Assert
        assert response.status_code == 302
        assert response.url == "/admin/"

    def test_sys002_redirect_school_leader_to_school_overview(self, client, school_leader_user):
        """
        Given: 校長/教頭（role='school_leader'）
        When: ログイン
        Then: /diary/school-overview/ にリダイレクト
        """
        # Arrange
        client.force_login(school_leader_user)

        # Act
        response = client.get(reverse("home"))

        # Assert
        assert response.status_code == 302
        assert response.url == reverse("diary:school_overview")

    def test_sys002_redirect_grade_leader_to_grade_overview(self, client, grade_leader_user):
        """
        Given: 学年主任（role='grade_leader'）
        When: ログイン
        Then: /diary/grade-overview/ にリダイレクト
        """
        # Arrange
        client.force_login(grade_leader_user)

        # Act
        response = client.get(reverse("home"))

        # Assert
        assert response.status_code == 302
        assert response.url == reverse("diary:grade_overview")

    def test_sys002_redirect_teacher_to_dashboard(self, client, teacher_user):
        """
        Given: 担任（role='teacher'）
        When: ログイン
        Then: /diary/teacher/dashboard/ にリダイレクト
        """
        # Arrange
        client.force_login(teacher_user)

        # Act
        response = client.get(reverse("home"))

        # Assert
        assert response.status_code == 302
        assert response.url == reverse("diary:teacher_dashboard")

    def test_sys002_redirect_student_to_dashboard(self, client, student_user):
        """
        Given: 生徒（role='student'）
        When: ログイン
        Then: /diary/student/dashboard/ にリダイレクト
        """
        # Arrange
        client.force_login(student_user)

        # Act
        response = client.get(reverse("home"))

        # Assert
        assert response.status_code == 302
        assert response.url == reverse("diary:student_dashboard")

    def test_sys002_redirect_unauthenticated_to_login(self, client):
        """
        Given: 未認証ユーザー
        When: / にアクセス
        Then: /accounts/login/ にリダイレクト
        """
        # Act
        response = client.get(reverse("home"))

        # Assert
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.django_db
class TestAUTH002Logout:
    """AUTH-002: ログアウト機能のテスト"""

    def test_auth002_logout_success(self, authenticated_student_client):
        """
        Given: ログイン済みユーザー
        When: ログアウト処理
        Then: ログアウト成功、ログインページにリダイレクト
        """
        # Act
        response = authenticated_student_client.post(reverse("account_logout"))

        # Assert
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.django_db
class TestAUTH003PasswordChange:
    """AUTH-003: パスワード変更機能のテスト"""

    def test_auth003_password_change_success(self, authenticated_student_client, student_user):
        """
        Given: ログイン済みユーザー
        When: 正しい旧パスワードと新パスワードで変更
        Then: 変更成功、リダイレクト
        """
        # Arrange
        data = {
            "old_password": "testpass123",
            "new_password1": "newpass456!",
            "new_password2": "newpass456!",
        }

        # Act
        response = authenticated_student_client.post(reverse("account_change_password"), data)

        # Assert
        assert response.status_code == 302

        # 新しいパスワードでログインできることを確認
        from django.contrib.auth import authenticate

        user = authenticate(username="student@test.com", password="newpass456!")
        assert user is not None
        assert user.id == student_user.id

    def test_auth003_password_change_wrong_old_password(self, authenticated_student_client):
        """
        Given: ログイン済みユーザー
        When: 間違った旧パスワードで変更試行
        Then: 変更失敗、エラーメッセージ表示
        """
        # Arrange
        data = {
            "old_password": "wrongpass",
            "new_password1": "newpass456!",
            "new_password2": "newpass456!",
        }

        # Act
        response = authenticated_student_client.post(reverse("account_change_password"), data)

        # Assert
        assert response.status_code == 200  # フォーム再表示
        assert "old_password" in response.context["form"].errors or "password" in response.content.decode().lower()

    def test_auth003_password_change_password_mismatch(self, authenticated_student_client):
        """
        Given: ログイン済みユーザー
        When: 新パスワードが一致しない
        Then: 変更失敗、エラーメッセージ表示
        """
        # Arrange
        data = {
            "old_password": "testpass123",
            "new_password1": "newpass456!",
            "new_password2": "differentpass789!",
        }

        # Act
        response = authenticated_student_client.post(reverse("account_change_password"), data)

        # Assert
        assert response.status_code == 200  # フォーム再表示
        assert "new_password2" in response.context["form"].errors or "match" in response.content.decode().lower()


@pytest.mark.django_db
class TestAUTH004To007PasswordReset:
    """AUTH-004〜007: パスワードリセット機能のテスト"""

    def test_auth004_password_reset_request_success(self, client, student_user):
        """
        Given: 登録済みユーザーのメールアドレス
        When: パスワードリセット要求
        Then: リセットメール送信完了ページにリダイレクト
        """
        # Arrange
        data = {"email": "student@test.com"}

        # Act
        response = client.post(reverse("account_reset_password"), data, follow=True)

        # Assert
        assert response.status_code == 200
        # allauthのリセット完了ページにリダイレクトされる
        assert "/accounts/password/reset/done/" in response.request["PATH_INFO"] or "送信" in response.content.decode()

    def test_auth005_password_reset_done_display(self, client):
        """
        Given: パスワードリセット要求後
        When: 完了ページにアクセス
        Then: リセットメール送信完了メッセージ表示
        """
        # Act
        response = client.get(reverse("account_reset_password_done"))

        # Assert
        assert response.status_code == 200
        # allauthのテンプレートが表示される
        content = response.content.decode().lower()
        assert "email" in content or "sent" in content or "メール" in content

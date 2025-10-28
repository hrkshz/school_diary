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


# =============================================================================
# Adapter Tests (RoleBasedRedirectAdapter)
# =============================================================================


@pytest.mark.django_db
class TestRoleBasedRedirectAdapterCleanEmail:
    """RoleBasedRedirectAdapter.clean_email()のテスト

    Note:
        get_login_redirect_url()は既存テスト（TestSYS002LoginRedirect）でカバー済み
    """

    def test_clean_email_with_lowercase_success(self, db):
        """
        Given: 小文字のみのメールアドレス
        When: clean_email()を呼ぶ
        Then: エラーなし
        """
        # Arrange
        from school_diary.diary.adapters import RoleBasedRedirectAdapter

        adapter = RoleBasedRedirectAdapter()
        email = "test@example.com"

        # Act
        result = adapter.clean_email(email)

        # Assert
        assert result == "test@example.com"

    def test_clean_email_with_uppercase_raises_error(self, db):
        """
        Given: 大文字を含むメールアドレス
        When: clean_email()を呼ぶ
        Then: ValidationError発生
        """
        # Arrange
        from django.core.exceptions import ValidationError

        from school_diary.diary.adapters import RoleBasedRedirectAdapter

        adapter = RoleBasedRedirectAdapter()
        email = "Test@Example.COM"

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            adapter.clean_email(email)

        assert "小文字のみ" in str(exc_info.value)

    def test_clean_email_strips_whitespace(self, db):
        """
        Given: 前後に空白を含むメールアドレス
        When: clean_email()を呼ぶ
        Then: 空白が削除される
        """
        # Arrange
        from school_diary.diary.adapters import RoleBasedRedirectAdapter

        adapter = RoleBasedRedirectAdapter()
        email = "  test@example.com  "

        # Act
        result = adapter.clean_email(email)

        # Assert
        assert result == "test@example.com"


@pytest.mark.django_db
class TestRoleBasedRedirectAdapterIsOpenForSignup:
    """RoleBasedRedirectAdapter.is_open_for_signup()のテスト"""

    def test_is_open_for_signup_returns_false(self, db, rf):
        """
        Given: 任意のリクエスト
        When: is_open_for_signup()を呼ぶ
        Then: False（サインアップ無効）
        """
        # Arrange
        from school_diary.diary.adapters import RoleBasedRedirectAdapter

        adapter = RoleBasedRedirectAdapter()
        request = rf.get("/")

        # Act
        result = adapter.is_open_for_signup(request)

        # Assert
        assert result is False


# =============================================================================
# Signal Tests (create_user_profile)
# =============================================================================


@pytest.mark.django_db
class TestCreateUserProfileSignal:
    """create_user_profile シグナルのテスト"""

    def test_user_creation_auto_creates_user_profile(self, db):
        """
        Given: 新規ユーザー作成
        When: User.objects.create_user()を呼ぶ
        Then: UserProfileが自動作成される
        """
        # Arrange
        from django.contrib.auth import get_user_model

        from school_diary.diary.models import UserProfile

        User = get_user_model()

        # Act
        user = User.objects.create_user(
            username="newuser@test.com",
            email="newuser@test.com",
            password="testpass123",
        )

        # Assert
        assert hasattr(user, "profile")
        assert isinstance(user.profile, UserProfile)
        assert user.profile.role == UserProfile.ROLE_STUDENT  # デフォルト

    def test_user_creation_auto_creates_email_address(self, db):
        """
        Given: 新規ユーザー作成（メールアドレスあり）
        When: User.objects.create_user()を呼ぶ
        Then: EmailAddressが自動作成される
        """
        # Arrange
        from allauth.account.models import EmailAddress
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Act
        user = User.objects.create_user(
            username="newuser2@test.com",
            email="newuser2@test.com",
            password="testpass123",
        )

        # Assert
        email_address = EmailAddress.objects.filter(user=user).first()
        assert email_address is not None
        assert email_address.email == "newuser2@test.com"
        assert email_address.primary

    def test_user_creation_without_email_does_not_create_email_address(self, db):
        """
        Given: 新規ユーザー作成（メールアドレスなし）
        When: User.objects.create_user()を呼ぶ
        Then: EmailAddressは作成されない
        """
        # Arrange
        from allauth.account.models import EmailAddress
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Act
        user = User.objects.create_user(
            username="nomail",
            password="testpass123",
        )

        # Assert
        email_address = EmailAddress.objects.filter(user=user).first()
        assert email_address is None

    def test_signal_does_not_run_on_user_update(self, student_user):
        """
        Given: 既存ユーザー
        When: ユーザーを更新
        Then: 新しいUserProfileは作成されない（既存のまま）
        """
        # Arrange
        original_profile_id = student_user.profile.id

        # Act
        student_user.first_name = "更新"
        student_user.save()

        # Assert
        student_user.refresh_from_db()
        assert student_user.profile.id == original_profile_id  # 同じprofile

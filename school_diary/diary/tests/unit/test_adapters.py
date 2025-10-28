"""
Unit Tests for Adapters

このモジュールは以下のアダプターロジックをテストします:
- RoleBasedRedirectAdapter.clean_email(): 大文字検証
- RoleBasedRedirectAdapter.is_open_for_signup(): サインアップ無効化

Priority: P1（高）

Note:
    get_login_redirect_url()は既存テスト（test_auth_features.py::TestSYS002LoginRedirect）
    でカバー済みのため、ここでは省略
"""

import pytest
from django.core.exceptions import ValidationError

from school_diary.diary.adapters import RoleBasedRedirectAdapter


@pytest.mark.django_db
class TestRoleBasedRedirectAdapterCleanEmail:
    """RoleBasedRedirectAdapter.clean_email()のテスト"""

    def test_clean_email_with_lowercase_success(self, db):
        """
        Given: 小文字のみのメールアドレス
        When: clean_email()を呼ぶ
        Then: エラーなし
        """
        # Arrange
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
        adapter = RoleBasedRedirectAdapter()
        request = rf.get("/")

        # Act
        result = adapter.is_open_for_signup(request)

        # Assert
        assert result is False

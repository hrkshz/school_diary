"""
Unit Tests for Signals

このモジュールは以下のシグナルをテストします:
- create_user_profile: User作成時にUserProfile自動作成
- create_user_profile: User作成時にEmailAddress自動作成

Priority: P1（高）
"""

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

from school_diary.diary.models import UserProfile

User = get_user_model()


@pytest.mark.django_db
class TestCreateUserProfileSignal:
    """create_user_profile シグナルのテスト"""

    def test_user_creation_auto_creates_user_profile(self, db):
        """
        Given: 新規ユーザー作成
        When: User.objects.create_user()を呼ぶ
        Then: UserProfileが自動作成される
        """
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

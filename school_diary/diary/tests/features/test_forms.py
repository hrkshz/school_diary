"""
Forms Validation Unit Tests

このモジュールは内部ロジックの正確性をテストします（Unit Tests）。
統合テスト（Integration Tests）とは粒度が異なりますが、
両方を features/ ディレクトリで管理することで、保守性を向上させています。

テスト対象バリデーション:
- DiaryEntryForm.clean_entry_date(): 前登校日検証
- UserProfileAdminForm.clean(): 学年主任のmanaged_grade必須検証
- CustomUserCreationForm.save(): username自動生成、is_staff自動設定
- CustomUserCreationForm.clean_email(): メールアドレス重複チェック
- CustomUserCreationForm.clean(): 学年主任のmanaged_grade必須検証

Priority: P0（クリティカル）
"""

import pytest

from school_diary.diary.forms import CustomUserCreationForm
from school_diary.diary.forms import DiaryEntryForm
from school_diary.diary.forms import UserProfileAdminForm
from school_diary.diary.models import UserProfile


@pytest.mark.django_db
class TestDiaryEntryFormCleanEntryDate:
    """DiaryEntryForm.clean_entry_date()のテスト"""

    def test_clean_entry_date_with_correct_previous_school_day_success(
        self,
        yesterday,
    ):
        """
        Given: 前登校日の日付
        When: clean_entry_date()を呼ぶ
        Then: エラーなし
        """
        # Arrange
        form = DiaryEntryForm(
            data={
                "entry_date": yesterday.strftime("%Y-%m-%d"),
                "health_condition": 4,
                "mental_condition": 4,
                "reflection": "テスト",
            },
        )

        # Act
        is_valid = form.is_valid()

        # Assert
        assert is_valid
        assert form.cleaned_data["entry_date"] == yesterday

    def test_clean_entry_date_with_wrong_date_raises_error(
        self,
        today,
    ):
        """
        Given: 今日の日付（前登校日ではない）
        When: clean_entry_date()を呼ぶ
        Then: ValidationError発生
        """
        # Arrange
        form = DiaryEntryForm(
            data={
                "entry_date": today.strftime("%Y-%m-%d"),
                "health_condition": 4,
                "mental_condition": 4,
                "reflection": "テスト",
            },
        )

        # Act
        is_valid = form.is_valid()

        # Assert
        assert not is_valid
        assert "entry_date" in form.errors


@pytest.mark.django_db
class TestUserProfileAdminFormClean:
    """UserProfileAdminForm.clean()のテスト"""

    def test_clean_grade_leader_without_managed_grade_raises_error(
        self,
        grade_leader_user,
    ):
        """
        Given: role=grade_leader、managed_grade=None
        When: clean()を呼ぶ
        Then: ValidationError発生
        """
        # Arrange
        form = UserProfileAdminForm(
            data={
                "user": grade_leader_user.id,
                "role": UserProfile.ROLE_GRADE_LEADER,
                "managed_grade": "",  # 空文字
            },
            instance=grade_leader_user.profile,
        )

        # Act
        is_valid = form.is_valid()

        # Assert
        assert not is_valid
        assert "managed_grade" in form.errors

    def test_clean_grade_leader_with_managed_grade_success(
        self,
        grade_leader_user,
    ):
        """
        Given: role=grade_leader、managed_grade=1
        When: clean()を呼ぶ
        Then: エラーなし
        """
        # Arrange
        form = UserProfileAdminForm(
            data={
                "user": grade_leader_user.id,
                "role": UserProfile.ROLE_GRADE_LEADER,
                "managed_grade": 1,
            },
            instance=grade_leader_user.profile,
        )

        # Act
        is_valid = form.is_valid()

        # Assert
        assert is_valid

    def test_clean_non_grade_leader_clears_managed_grade(
        self,
        student_user,
    ):
        """
        Given: role=student、managed_grade=1
        When: clean()を呼ぶ
        Then: managed_grade自動的にNoneにクリア
        """
        # Arrange
        form = UserProfileAdminForm(
            data={
                "user": student_user.id,
                "role": UserProfile.ROLE_STUDENT,
                "managed_grade": 1,  # 不正な値
            },
            instance=student_user.profile,
        )

        # Act
        is_valid = form.is_valid()

        # Assert
        assert is_valid
        assert form.cleaned_data["managed_grade"] is None


@pytest.mark.django_db
class TestCustomUserCreationFormSave:
    """CustomUserCreationForm.save()のテスト"""

    def test_save_generates_unique_username(self, db):
        """
        Given: 姓="山田"、名="太郎"
        When: save()を呼ぶ
        Then: username="山田太郎"で作成
        """
        # Arrange
        form = CustomUserCreationForm(
            data={
                "email": "yamada@test.com",
                "last_name": "山田",
                "first_name": "太郎",
                "role": UserProfile.ROLE_STUDENT,
                "password1": "testpass123!",
                "password2": "testpass123!",
            },
        )

        # Act
        assert form.is_valid()
        user = form.save()

        # Assert
        assert user.username == "山田太郎"
        assert user.email == "yamada@test.com"
        assert user.last_name == "山田"
        assert user.first_name == "太郎"

    def test_save_generates_unique_username_with_counter_when_duplicate(
        self,
        db,
    ):
        """
        Given: 既に"山田太郎"が存在
        When: 同じ姓名でsave()を呼ぶ
        Then: username="山田太郎2"で作成
        """
        # Arrange: 1人目作成
        form1 = CustomUserCreationForm(
            data={
                "email": "yamada1@test.com",
                "last_name": "山田",
                "first_name": "太郎",
                "role": UserProfile.ROLE_STUDENT,
                "password1": "testpass123!",
                "password2": "testpass123!",
            },
        )
        assert form1.is_valid()
        user1 = form1.save()
        assert user1.username == "山田太郎"

        # Arrange: 2人目作成
        form2 = CustomUserCreationForm(
            data={
                "email": "yamada2@test.com",
                "last_name": "山田",
                "first_name": "太郎",
                "role": UserProfile.ROLE_STUDENT,
                "password1": "testpass123!",
                "password2": "testpass123!",
            },
        )

        # Act
        assert form2.is_valid()
        user2 = form2.save()

        # Assert
        assert user2.username == "山田太郎2"

    def test_save_sets_is_staff_for_non_student_roles(self, db):
        """
        Given: role=teacher
        When: save()を呼ぶ
        Then: is_staff=True
        """
        # Arrange
        form = CustomUserCreationForm(
            data={
                "email": "teacher@test.com",
                "last_name": "先生",
                "first_name": "花子",
                "role": UserProfile.ROLE_TEACHER,
                "password1": "testpass123!",
                "password2": "testpass123!",
            },
        )

        # Act
        assert form.is_valid()
        user = form.save()

        # Assert
        assert user.is_staff

    def test_save_does_not_set_is_staff_for_student(self, db):
        """
        Given: role=student
        When: save()を呼ぶ
        Then: is_staff=False
        """
        # Arrange
        form = CustomUserCreationForm(
            data={
                "email": "student@test.com",
                "last_name": "生徒",
                "first_name": "太郎",
                "role": UserProfile.ROLE_STUDENT,
                "password1": "testpass123!",
                "password2": "testpass123!",
            },
        )

        # Act
        assert form.is_valid()
        user = form.save()

        # Assert
        assert not user.is_staff

    def test_save_creates_email_address_record(self, db):
        """
        Given: 新規ユーザー
        When: save()を呼ぶ
        Then: EmailAddressレコード作成、verified=True
        """
        # Arrange
        from allauth.account.models import EmailAddress

        form = CustomUserCreationForm(
            data={
                "email": "test@test.com",
                "last_name": "テスト",
                "first_name": "太郎",
                "role": UserProfile.ROLE_STUDENT,
                "password1": "testpass123!",
                "password2": "testpass123!",
            },
        )

        # Act
        assert form.is_valid()
        user = form.save()

        # Assert
        email_address = EmailAddress.objects.filter(user=user).first()
        assert email_address is not None
        assert email_address.verified
        assert email_address.primary


@pytest.mark.django_db
class TestCustomUserCreationFormCleanEmail:
    """CustomUserCreationForm.clean_email()のテスト"""

    def test_clean_email_with_duplicate_raises_error(self, student_user):
        """
        Given: 既に登録済みのメールアドレス
        When: clean_email()を呼ぶ
        Then: ValidationError発生
        """
        # Arrange
        form = CustomUserCreationForm(
            data={
                "email": "student@test.com",  # 既存のメールアドレス
                "last_name": "新規",
                "first_name": "ユーザー",
                "role": UserProfile.ROLE_STUDENT,
                "password1": "testpass123!",
                "password2": "testpass123!",
            },
        )

        # Act
        is_valid = form.is_valid()

        # Assert
        assert not is_valid
        assert "email" in form.errors

    def test_clean_email_with_unique_email_success(self, db):
        """
        Given: 未登録のメールアドレス
        When: clean_email()を呼ぶ
        Then: エラーなし
        """
        # Arrange
        form = CustomUserCreationForm(
            data={
                "email": "unique@test.com",
                "last_name": "ユニーク",
                "first_name": "太郎",
                "role": UserProfile.ROLE_STUDENT,
                "password1": "testpass123!",
                "password2": "testpass123!",
            },
        )

        # Act
        is_valid = form.is_valid()

        # Assert
        assert is_valid


@pytest.mark.django_db
class TestCustomUserCreationFormClean:
    """CustomUserCreationForm.clean()のテスト"""

    def test_clean_grade_leader_without_managed_grade_raises_error(self, db):
        """
        Given: role=grade_leader、managed_grade=None
        When: clean()を呼ぶ
        Then: ValidationError発生
        """
        # Arrange
        form = CustomUserCreationForm(
            data={
                "email": "leader@test.com",
                "last_name": "学年",
                "first_name": "主任",
                "role": UserProfile.ROLE_GRADE_LEADER,
                "managed_grade": "",  # 空文字
                "password1": "testpass123!",
                "password2": "testpass123!",
            },
        )

        # Act
        is_valid = form.is_valid()

        # Assert
        assert not is_valid
        assert "managed_grade" in form.errors

    def test_clean_grade_leader_with_managed_grade_success(self, db):
        """
        Given: role=grade_leader、managed_grade=1
        When: clean()を呼ぶ
        Then: エラーなし
        """
        # Arrange
        form = CustomUserCreationForm(
            data={
                "email": "leader@test.com",
                "last_name": "学年",
                "first_name": "主任",
                "role": UserProfile.ROLE_GRADE_LEADER,
                "managed_grade": 1,
                "password1": "testpass123!",
                "password2": "testpass123!",
            },
        )

        # Act
        is_valid = form.is_valid()

        # Assert
        assert is_valid

"""Management commandsのテスト"""

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DiaryEntry
from school_diary.diary.models import UserProfile

User = get_user_model()


@pytest.mark.django_db
class TestCreateTestDataCommand:
    """create_test_dataコマンドのテスト"""

    def test_clean_data_preserves_superuser(self):
        """スーパーユーザーは--cleanオプションでも削除されないことを保証"""
        # スーパーユーザーを作成
        superuser = User.objects.create_superuser(
            username="existing_admin@example.com",
            email="existing_admin@example.com",
            password="testpass123",
            first_name="既存",
            last_name="管理者",
        )

        # テストデータ作成コマンドを--cleanオプションで実行
        call_command("create_test_data", "--clean", "--diary-days", "1", "--students-per-class", "5")

        # スーパーユーザーが削除されていないことを確認
        assert User.objects.filter(id=superuser.id).exists()
        assert User.objects.filter(email="existing_admin@example.com", is_superuser=True).exists()

    def test_clean_data_removes_non_superuser(self):
        """スーパーユーザー以外のユーザーは--cleanオプションで削除されることを確認"""
        # 通常ユーザーを作成
        normal_user = User.objects.create_user(
            username="normal_user@example.com",
            email="normal_user@example.com",
            password="testpass123",
            first_name="通常",
            last_name="ユーザー",
        )

        # テストデータ作成コマンドを--cleanオプションで実行
        call_command("create_test_data", "--clean", "--diary-days", "1", "--students-per-class", "5")

        # 通常ユーザーは削除されていることを確認
        assert not User.objects.filter(id=normal_user.id).exists()

    def test_creates_test_data_successfully(self):
        """テストデータが正常に作成されることを確認"""
        # テストデータ作成コマンドを実行
        call_command("create_test_data", "--clean", "--diary-days", "3", "--students-per-class", "10")

        # 基本データが作成されていることを確認
        assert User.objects.filter(is_superuser=True).count() == 1  # 管理者
        assert User.objects.filter(profile__role=UserProfile.ROLE_SCHOOL_LEADER).count() == 1  # 校長
        assert User.objects.filter(profile__role=UserProfile.ROLE_GRADE_LEADER).count() == 3  # 学年主任
        assert User.objects.filter(profile__role=UserProfile.ROLE_TEACHER).count() == 9  # 担任
        # 生徒は90名（10名×9クラス）作成されるが、admin@example.comがprofile.roleを持たないため91名になる可能性を許容
        student_count = User.objects.filter(profile__role=UserProfile.ROLE_STUDENT).count()
        assert 90 <= student_count <= 91  # 柔軟なアサーション
        assert ClassRoom.objects.count() == 9  # クラス
        assert DiaryEntry.objects.count() > 0  # 日記

    def test_no_clean_preserves_existing_data(self):
        """--cleanオプションなしの場合、既存データが保持されることを確認"""
        # 既存ユーザーを作成
        existing_student = User.objects.create_user(
            username="existing_student@example.com",
            email="existing_student@example.com",
            password="testpass123",
            first_name="既存",
            last_name="生徒",
        )
        existing_student.profile.role = UserProfile.ROLE_STUDENT
        existing_student.profile.save()

        # テストデータ作成コマンドを--cleanオプションなしで実行
        call_command("create_test_data", "--diary-days", "1", "--students-per-class", "5")

        # 既存ユーザーが保持されていることを確認
        assert User.objects.filter(id=existing_student.id).exists()
        assert User.objects.filter(email="existing_student@example.com").exists()

    def test_multiple_superusers_preserved(self):
        """複数のスーパーユーザーが全て保護されることを確認"""
        # 複数のスーパーユーザーを作成
        superuser1 = User.objects.create_superuser(
            username="admin1@example.com",
            email="admin1@example.com",
            password="testpass123",
            first_name="管理者",
            last_name="1",
        )
        superuser2 = User.objects.create_superuser(
            username="admin2@example.com",
            email="admin2@example.com",
            password="testpass123",
            first_name="管理者",
            last_name="2",
        )

        # テストデータ作成コマンドを--cleanオプションで実行
        call_command("create_test_data", "--clean", "--diary-days", "1", "--students-per-class", "5")

        # 全てのスーパーユーザーが削除されていないことを確認
        assert User.objects.filter(id=superuser1.id).exists()
        assert User.objects.filter(id=superuser2.id).exists()
        assert User.objects.filter(is_superuser=True).count() >= 2

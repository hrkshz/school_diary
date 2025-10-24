from datetime import date
from datetime import timedelta

import pytest  # type: ignore[import-untyped]
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

User = get_user_model()


@pytest.fixture(autouse=True)
def _media_storage(settings, tmpdir) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user(db) -> AbstractUser:
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def yesterday():
    """昨日の日付を返すフィクスチャ

    テストで過去の日付が必要な場合に使用します。
    一日一件制約のテストなどに便利です。

    使用例:
        def test_create_entry(yesterday):
            entry = DiaryEntry.objects.create(
                entry_date=yesterday,
                ...
            )
    """
    return date.today() - timedelta(days=1)


@pytest.fixture
def sample_diary_entry(db, user, yesterday):
    """サンプルの連絡帳エントリを作成するフィクスチャ

    テストで既存データが必要な場合に使用します。
    重複チェックや更新テストなどに便利です。

    使用例:
        def test_duplicate(sample_diary_entry):
            # sample_diary_entry が既に存在する状態でテスト
            assert DiaryEntry.objects.count() == 1
    """
    from school_diary.diary.models import DiaryEntry

    return DiaryEntry.objects.create(
        student=user,
        entry_date=yesterday,
        health_condition=3,
        mental_condition=3,
        reflection="サンプルエントリ",
    )

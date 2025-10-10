"""
Tests for diary app.

このファイルは DiaryEntry モデル、DiaryEntryForm、DiaryCreateView の
自動テストを提供します。

テスト実行方法:
    dj pytest school_diary/diary/tests.py -v
    または
    dj pytest school_diary/diary/tests.py::TestDiaryCreateView -v
"""

from datetime import date
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import Client
from django.urls import reverse

from school_diary.diary.forms import DiaryEntryForm
from school_diary.diary.models import DiaryEntry

User = get_user_model()


@pytest.fixture
def test_user(db):
    """テストユーザーを作成するフィクスチャ"""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def test_user2(db):
    """2人目のテストユーザーを作成するフィクスチャ"""
    return User.objects.create_user(
        username="testuser2",
        email="test2@example.com",
        password="testpass123",
    )


@pytest.fixture
def authenticated_client(test_user):
    """認証済みクライアントを作成するフィクスチャ"""
    client = Client()
    client.force_login(test_user)
    return client


@pytest.mark.django_db
class TestDiaryCreateView:
    """DiaryCreateView の統合テスト

    このテストクラスは、連絡帳作成ページの動作を検証します。
    ブラウザでの手動テストと同じことをコードで自動化します。
    """

    def test_get_request_authenticated_user(self, authenticated_client):
        """
        【テスト1】ログイン済みユーザーのGETリクエスト

        期待される動作:
        - ステータスコード 200
        - diary/diary_create.html テンプレートが使用される
        - フォームが表示される
        """
        url = reverse("diary:diary_create")
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "diary/diary_create.html" in [t.name for t in response.templates]
        assert "form" in response.context
        assert isinstance(response.context["form"], DiaryEntryForm)

    def test_get_request_unauthenticated_user(self):
        """
        【テスト2】未ログインユーザーのGETリクエスト

        期待される動作:
        - ログインページへリダイレクト（302）
        - リダイレクト先が /accounts/login/?next=/diary/create/
        """
        client = Client()
        url = reverse("diary:diary_create")
        response = client.get(url)

        assert response.status_code == 302
        assert "/accounts/login/" in response.url
        assert f"next={url}" in response.url

    def test_post_request_valid_data(self, authenticated_client, test_user):
        """
        【テスト3】有効なデータでのPOSTリクエスト

        期待される動作:
        - DiaryEntry が作成される
        - student が自動設定される
        - student_dashboard へリダイレクト（302）
        - 成功メッセージが表示される
        """
        url = reverse("diary:diary_create")
        yesterday = date.today() - timedelta(days=1)

        # DiaryEntry が0件であることを確認
        assert DiaryEntry.objects.count() == 0

        # 有効なデータでPOST
        response = authenticated_client.post(
            url,
            {
                "entry_date": yesterday.isoformat(),
                "health_condition": "3",
                "mental_condition": "4",
                "reflection": "今日はテストを書きました。",
            },
        )

        # リダイレクトを確認
        assert response.status_code == 302
        assert response.url == reverse("diary:student_dashboard")

        # DiaryEntry が作成されたことを確認
        assert DiaryEntry.objects.count() == 1
        entry = DiaryEntry.objects.first()
        assert entry.student == test_user
        assert entry.entry_date == yesterday
        assert entry.health_condition == 3  # IntegerField
        assert entry.mental_condition == 4  # IntegerField
        assert entry.reflection == "今日はテストを書きました。"

        # 成功メッセージを確認
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert "連絡帳を作成しました" in str(messages[0])

    def test_post_request_duplicate_date(self, authenticated_client, test_user):
        """
        【テスト4】一日一件制約のテスト（重複エラー）

        期待される動作:
        - 同じ日付のエントリは作成されない
        - student_dashboard へリダイレクト（302）
        - エラーメッセージが表示される
        """
        yesterday = date.today() - timedelta(days=1)

        # 最初のエントリを作成
        DiaryEntry.objects.create(
            student=test_user,
            entry_date=yesterday,
            health_condition="3",
            mental_condition="3",
            reflection="最初のエントリ",
        )
        assert DiaryEntry.objects.count() == 1

        # 同じ日付で2つ目のエントリを作成しようとする
        url = reverse("diary:diary_create")
        response = authenticated_client.post(
            url,
            {
                "entry_date": yesterday.isoformat(),
                "health_condition": "4",
                "mental_condition": "4",
                "reflection": "2つ目のエントリ（作成されないはず）",
            },
        )

        # リダイレクトを確認
        assert response.status_code == 302
        assert response.url == reverse("diary:student_dashboard")

        # DiaryEntry が増えていないことを確認
        assert DiaryEntry.objects.count() == 1
        entry = DiaryEntry.objects.first()
        assert entry.reflection == "最初のエントリ"  # 元のまま

        # エラーメッセージを確認
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert f"{yesterday}の連絡帳は既に作成済みです" in str(messages[0])

    def test_post_request_different_users(
        self,
        authenticated_client,
        test_user,
        test_user2,
    ):
        """
        【テスト5】異なるユーザーは同じ日付でエントリ可能

        期待される動作:
        - ユーザー1が作成した日付でも、ユーザー2は作成できる
        - 一日一件制約はユーザーごとに適用される
        """
        yesterday = date.today() - timedelta(days=1)

        # ユーザー1のエントリ作成
        DiaryEntry.objects.create(
            student=test_user,
            entry_date=yesterday,
            health_condition="3",
            mental_condition="3",
            reflection="ユーザー1のエントリ",
        )

        # ユーザー2でログイン
        client2 = Client()
        client2.force_login(test_user2)

        # ユーザー2で同じ日付のエントリ作成
        url = reverse("diary:diary_create")
        response = client2.post(
            url,
            {
                "entry_date": yesterday.isoformat(),
                "health_condition": "4",
                "mental_condition": "4",
                "reflection": "ユーザー2のエントリ",
            },
        )

        # 成功を確認
        assert response.status_code == 302
        assert DiaryEntry.objects.count() == 2
        assert DiaryEntry.objects.filter(student=test_user).count() == 1
        assert DiaryEntry.objects.filter(student=test_user2).count() == 1


@pytest.mark.django_db
class TestDiaryEntryForm:
    """DiaryEntryForm のユニットテスト

    フォームのバリデーションを個別に検証します。
    """

    def test_form_valid_data(self):
        """
        【テスト6】有効なデータでのフォームバリデーション

        期待される動作:
        - is_valid() が True
        """
        yesterday = date.today() - timedelta(days=1)
        form = DiaryEntryForm(
            data={
                "entry_date": yesterday,
                "health_condition": "3",
                "mental_condition": "4",
                "reflection": "テスト用の振り返り",
            },
        )
        assert form.is_valid()

    def test_form_missing_required_fields(self):
        """
        【テスト7】必須フィールドが欠けている場合

        期待される動作:
        - is_valid() が False
        - エラーメッセージが含まれる
        """
        form = DiaryEntryForm(data={})
        assert not form.is_valid()
        assert "entry_date" in form.errors
        assert "health_condition" in form.errors
        assert "mental_condition" in form.errors
        assert "reflection" in form.errors


@pytest.mark.django_db
class TestDiaryEntry:
    """DiaryEntry モデルのユニットテスト

    モデルの基本的な動作を検証します。
    """

    def test_create_diary_entry(self, test_user):
        """
        【テスト8】DiaryEntry の作成

        期待される動作:
        - DiaryEntry が正常に作成される
        - 各フィールドの値が正しい
        """
        yesterday = date.today() - timedelta(days=1)
        entry = DiaryEntry.objects.create(
            student=test_user,
            entry_date=yesterday,
            health_condition=3,  # IntegerField
            mental_condition=4,  # IntegerField
            reflection="モデルテスト",
        )

        assert entry.student == test_user
        assert entry.entry_date == yesterday
        assert entry.health_condition == 3  # IntegerField
        assert entry.mental_condition == 4  # IntegerField
        assert entry.reflection == "モデルテスト"
        assert entry.read_by is None  # 未読
        assert entry.read_at is None

    def test_str_method(self, test_user):
        """
        【テスト9】__str__ メソッド

        期待される動作:
        - __str__() が適切な文字列を返す
        """
        yesterday = date.today() - timedelta(days=1)
        entry = DiaryEntry.objects.create(
            student=test_user,
            entry_date=yesterday,
            health_condition=3,  # IntegerField
            mental_condition=3,  # IntegerField
            reflection="テスト",
        )

        expected = f"{test_user.username} - {yesterday}"
        assert str(entry) == expected

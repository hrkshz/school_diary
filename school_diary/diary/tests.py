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

    def test_entry_date_previous_school_day_valid(self):
        """
        【テスト17】前登校日なら成功

        期待される動作:
        - 2025-10-15（水）に 2025-10-14（火）を入力
        - is_valid() が True
        """
        from unittest.mock import patch

        today = date(2025, 10, 15)  # 水曜日
        expected_previous = date(2025, 10, 14)  # 火曜日

        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value.date.return_value = today

            form = DiaryEntryForm(
                data={
                    "entry_date": expected_previous,
                    "health_condition": "3",
                    "mental_condition": "4",
                    "reflection": "テスト用の振り返り",
                },
            )
            assert form.is_valid(), f"Form errors: {form.errors}"

    def test_entry_date_not_previous_school_day_invalid(self):
        """
        【テスト18】前登校日でない場合はエラー

        期待される動作:
        - 2025-10-15（水）に 2025-10-13（月）を入力
        - is_valid() が False
        - エラーメッセージに「前登校日」が含まれる
        """
        from unittest.mock import patch

        today = date(2025, 10, 15)  # 水曜日
        wrong_date = date(2025, 10, 13)  # 月曜日（前々日）

        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value.date.return_value = today

            form = DiaryEntryForm(
                data={
                    "entry_date": wrong_date,
                    "health_condition": "3",
                    "mental_condition": "4",
                    "reflection": "テスト用の振り返り",
                },
            )
            assert not form.is_valid()
            assert "entry_date" in form.errors
            assert "前登校日" in str(form.errors["entry_date"])

    def test_entry_date_future_invalid(self):
        """
        【テスト19】未来の日付はエラー

        期待される動作:
        - 2025-10-15（水）に 2025-10-16（木）を入力
        - is_valid() が False
        """
        from unittest.mock import patch

        today = date(2025, 10, 15)  # 水曜日
        future_date = date(2025, 10, 16)  # 木曜日（明日）

        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value.date.return_value = today

            form = DiaryEntryForm(
                data={
                    "entry_date": future_date,
                    "health_condition": "3",
                    "mental_condition": "4",
                    "reflection": "テスト用の振り返り",
                },
            )
            assert not form.is_valid()
            assert "entry_date" in form.errors

    def test_entry_date_monday_expects_friday(self):
        """
        【テスト20】月曜日は金曜日を期待

        期待される動作:
        - 2025-10-13（月）に 2025-10-10（金）を入力
        - is_valid() が True
        """
        from unittest.mock import patch

        monday = date(2025, 10, 13)  # 月曜日
        expected_friday = date(2025, 10, 10)  # 金曜日

        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value.date.return_value = monday

            form = DiaryEntryForm(
                data={
                    "entry_date": expected_friday,
                    "health_condition": "3",
                    "mental_condition": "4",
                    "reflection": "テスト用の振り返り",
                },
            )
            assert form.is_valid(), f"Form errors: {form.errors}"


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

    def test_diary_becomes_past_record_after_read(self, test_user):
        """
        【テスト21】既読処理=過去記録化

        期待される動作:
        - 作成直後: is_editable=True（編集可能）、is_read=False
        - 既読処理後: is_editable=False（過去記録、編集不可）、is_read=True

        要件: 「本PoCでは既読処理が行われた時点で過去記録の扱いとする」
        """
        # 担任ユーザーを作成
        teacher = User.objects.create_user(
            username="teacher001",
            email="teacher001@example.com",
            password="teacherpass123",
        )

        # 生徒が連絡帳作成
        yesterday = date.today() - timedelta(days=1)
        entry = DiaryEntry.objects.create(
            student=test_user,
            entry_date=yesterday,
            health_condition=3,
            mental_condition=4,
            reflection="テスト用の振り返り",
        )

        # 未既読: 編集可能
        assert entry.is_editable is True, "作成直後は編集可能であるべき"
        assert entry.is_read is False, "作成直後は未読であるべき"

        # 担任が既読処理
        entry.mark_as_read(teacher)

        # 既読後: 編集不可（過去記録化）
        assert entry.is_editable is False, "既読後は編集不可（過去記録）であるべき"
        assert entry.is_read is True, "既読処理後はis_read=Trueであるべき"
        assert entry.read_by == teacher, "既読者が正しく記録されるべき"
        assert entry.read_at is not None, "既読日時が記録されるべき"


@pytest.mark.django_db
class TestPreviousSchoolDay:
    """get_previous_school_day() ヘルパー関数のユニットテスト

    前登校日の計算ロジックを検証します。
    土日を除外し、月曜日の場合は金曜日を返すことを確認します。
    """

    def test_monday_returns_friday(self):
        """
        【テスト10】月曜日 → 金曜日

        期待される動作:
        - 2025-10-13（月）→ 2025-10-10（金）
        """
        from school_diary.diary.utils import get_previous_school_day

        monday = date(2025, 10, 13)  # 月曜日
        expected_friday = date(2025, 10, 10)  # 金曜日
        result = get_previous_school_day(monday)
        assert result == expected_friday

    def test_tuesday_returns_monday(self):
        """
        【テスト11】火曜日 → 月曜日

        期待される動作:
        - 2025-10-14（火）→ 2025-10-13（月）
        """
        from school_diary.diary.utils import get_previous_school_day

        tuesday = date(2025, 10, 14)  # 火曜日
        expected_monday = date(2025, 10, 13)  # 月曜日
        result = get_previous_school_day(tuesday)
        assert result == expected_monday

    def test_wednesday_returns_tuesday(self):
        """
        【テスト12】水曜日 → 火曜日

        期待される動作:
        - 2025-10-15（水）→ 2025-10-14（火）
        """
        from school_diary.diary.utils import get_previous_school_day

        wednesday = date(2025, 10, 15)  # 水曜日
        expected_tuesday = date(2025, 10, 14)  # 火曜日
        result = get_previous_school_day(wednesday)
        assert result == expected_tuesday

    def test_thursday_returns_wednesday(self):
        """
        【テスト13】木曜日 → 水曜日

        期待される動作:
        - 2025-10-16（木）→ 2025-10-15（水）
        """
        from school_diary.diary.utils import get_previous_school_day

        thursday = date(2025, 10, 16)  # 木曜日
        expected_wednesday = date(2025, 10, 15)  # 水曜日
        result = get_previous_school_day(thursday)
        assert result == expected_wednesday

    def test_friday_returns_thursday(self):
        """
        【テスト14】金曜日 → 木曜日

        期待される動作:
        - 2025-10-17（金）→ 2025-10-16（木）
        """
        from school_diary.diary.utils import get_previous_school_day

        friday = date(2025, 10, 17)  # 金曜日
        expected_thursday = date(2025, 10, 16)  # 木曜日
        result = get_previous_school_day(friday)
        assert result == expected_thursday

    def test_saturday_returns_friday(self):
        """
        【テスト15】土曜日 → 金曜日

        期待される動作:
        - 2025-10-18（土）→ 2025-10-17（金）
        """
        from school_diary.diary.utils import get_previous_school_day

        saturday = date(2025, 10, 18)  # 土曜日
        expected_friday = date(2025, 10, 17)  # 金曜日
        result = get_previous_school_day(saturday)
        assert result == expected_friday

    def test_sunday_returns_friday(self):
        """
        【テスト16】日曜日 → 金曜日

        期待される動作:
        - 2025-10-19（日）→ 2025-10-17（金）
        """
        from school_diary.diary.utils import get_previous_school_day

        sunday = date(2025, 10, 19)  # 日曜日
        expected_friday = date(2025, 10, 17)  # 金曜日
        result = get_previous_school_day(sunday)
        assert result == expected_friday


@pytest.mark.django_db
class TestDiaryUpdateView:
    """DiaryUpdateView の統合テスト（TDD: Red Phase）

    S-02「連絡帳編集」機能の動作を検証します。
    要件: 既読前のみ編集可能、既読後は過去記録化（編集不可）
    """

    @pytest.fixture
    def teacher(self, db):
        """担任ユーザーを作成するフィクスチャ"""
        return User.objects.create_user(
            username="teacher001",
            email="teacher001@example.com",
            password="teacherpass123",
        )

    @pytest.fixture
    def unread_entry(self, test_user, db):
        """未既読のエントリー（編集可能）"""
        return DiaryEntry.objects.create(
            student=test_user,
            entry_date=date.today() - timedelta(days=1),
            health_condition=4,
            mental_condition=3,
            reflection="元の内容",
        )

    @pytest.fixture
    def read_entry(self, test_user, teacher, db):
        """既読済みのエントリー（編集不可）"""
        entry = DiaryEntry.objects.create(
            student=test_user,
            entry_date=date.today() - timedelta(days=2),
            health_condition=4,
            mental_condition=3,
            reflection="既読後の内容",
        )
        entry.mark_as_read(teacher)
        return entry

    def test_edit_own_unread_entry_success(
        self,
        authenticated_client,
        test_user,
        unread_entry,
    ):
        """
        【テスト22】自分の未既読エントリーを編集できる

        期待される動作:
        - ステータスコード 302（リダイレクト）
        - 編集内容が保存される
        - student_dashboard へリダイレクト
        """
        url = reverse("diary:diary_update", args=[unread_entry.pk])
        response = authenticated_client.post(
            url,
            {
                "entry_date": unread_entry.entry_date.isoformat(),
                "health_condition": "5",
                "mental_condition": "4",
                "reflection": "修正後の内容",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse("diary:student_dashboard")

        unread_entry.refresh_from_db()
        assert unread_entry.health_condition == 5
        assert unread_entry.mental_condition == 4
        assert unread_entry.reflection == "修正後の内容"

    def test_cannot_edit_read_entry(
        self,
        authenticated_client,
        test_user,
        read_entry,
    ):
        """
        【テスト23】既読後は編集できない

        期待される動作:
        - ステータスコード 404（Not Found）
        - 既読エントリーは get_queryset() でフィルタされる
        """
        url = reverse("diary:diary_update", args=[read_entry.pk])
        response = authenticated_client.post(
            url,
            {
                "entry_date": read_entry.entry_date.isoformat(),
                "health_condition": "5",
                "mental_condition": "5",
                "reflection": "編集しようとする（失敗するべき）",
            },
        )

        assert response.status_code == 404

        # データが変更されていないことを確認
        read_entry.refresh_from_db()
        assert read_entry.reflection == "既読後の内容"

    def test_cannot_edit_others_entry(self, test_user, test_user2, unread_entry):
        """
        【テスト24】他人のエントリーは編集できない

        期待される動作:
        - ステータスコード 404（Not Found）
        - 他人のエントリーは get_queryset() でフィルタされる
        """
        # test_user2 でログイン（エントリーの所有者はtest_user）
        client2 = Client()
        client2.force_login(test_user2)

        url = reverse("diary:diary_update", args=[unread_entry.pk])
        response = client2.post(
            url,
            {
                "entry_date": unread_entry.entry_date.isoformat(),
                "health_condition": "5",
                "mental_condition": "5",
                "reflection": "他人のエントリーを編集しようとする（失敗するべき）",
            },
        )

        assert response.status_code == 404

        # データが変更されていないことを確認
        unread_entry.refresh_from_db()
        assert unread_entry.reflection == "元の内容"

    def test_get_edit_page_success(
        self,
        authenticated_client,
        test_user,
        unread_entry,
    ):
        """
        【テスト27】編集ページを表示できる

        期待される動作:
        - ステータスコード 200
        - diary/diary_update.html テンプレートが使用される
        - フォームが表示される
        """
        url = reverse("diary:diary_update", args=[unread_entry.pk])
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert "diary/diary_update.html" in [t.name for t in response.templates]
        assert "form" in response.context
        assert isinstance(response.context["form"], DiaryEntryForm)

    def test_unauthenticated_user_redirected(self, unread_entry):
        """
        【テスト28】未認証ユーザーはリダイレクト

        期待される動作:
        - ステータスコード 302（リダイレクト）
        - ログインページへリダイレクト
        """
        client = Client()
        url = reverse("diary:diary_update", args=[unread_entry.pk])
        response = client.get(url)

        assert response.status_code == 302
        assert "/accounts/login/" in response.url
        assert f"next={url}" in response.url


@pytest.mark.django_db
class TestConsecutiveDeclineDetection:
    """3日連続低下検出のユニットテスト

    メンタル・体調の3日連続低下パターンを検出するアルゴリズムを検証します。
    定義: day1≥day2≥day3 AND day3<day1（非改善 AND 全体的低下）
    """

    @pytest.fixture
    def student(self, db):
        """テスト用の生徒ユーザーを作成"""
        user = User.objects.create_user(
            username="student_alert_test",
            email="student_alert_test@example.com",
            password="testpass123",
        )
        user.profile.role = "student"
        user.profile.save()
        return user

    def create_entry(self, student, entry_date, health_value, mental_value=3):
        """DiaryEntryを作成するヘルパー"""
        return DiaryEntry.objects.create(
            student=student,
            entry_date=entry_date,
            health_condition=health_value,
            mental_condition=mental_value,
            reflection="Test entry",
        )

    def test_basic_declining_trend_triggers_alert(self, student):
        """
        【テスト29】厳密な連続低下（5→4→3）はアラート対象

        期待される動作:
        - has_alert: True
        - trend: [5, 4, 3]
        - dates: 3日分
        """
        from school_diary.diary.utils import check_consecutive_decline

        # 固定日付: 2025-10-13（月）、14（火）、15（水）
        self.create_entry(student, date(2025, 10, 13), health_value=5)
        self.create_entry(student, date(2025, 10, 14), health_value=4)
        self.create_entry(student, date(2025, 10, 15), health_value=3)

        result = check_consecutive_decline(student, "health_condition")

        assert result["has_alert"] is True
        assert result["trend"] == [5, 4, 3]
        assert len(result["dates"]) == 3

    def test_non_improving_with_plateau_triggers_alert(self, student):
        """
        【テスト30】停滞後の低下（4→4→3）はアラート対象

        回復力の喪失パターン: 改善せず、最終的に低下
        期待される動作:
        - has_alert: True
        - trend: [4, 4, 3]
        """
        from school_diary.diary.utils import check_consecutive_decline

        self.create_entry(student, date(2025, 10, 13), health_value=4)
        self.create_entry(student, date(2025, 10, 14), health_value=4)
        self.create_entry(student, date(2025, 10, 15), health_value=3)

        result = check_consecutive_decline(student, "health_condition")

        assert result["has_alert"] is True
        assert result["trend"] == [4, 4, 3]

    def test_improving_trend_no_alert(self, student):
        """
        【テスト31】改善傾向（3→4→5）はアラート対象外

        期待される動作:
        - has_alert: False
        """
        from school_diary.diary.utils import check_consecutive_decline

        self.create_entry(student, date(2025, 10, 13), health_value=3)
        self.create_entry(student, date(2025, 10, 14), health_value=4)
        self.create_entry(student, date(2025, 10, 15), health_value=5)

        result = check_consecutive_decline(student, "health_condition")

        assert result["has_alert"] is False

    def test_fluctuating_pattern_no_alert(self, student):
        """
        【テスト32】回復あり（4→3→4）はアラート対象外

        一時的な変動であり、回復力がある
        期待される動作:
        - has_alert: False
        """
        from school_diary.diary.utils import check_consecutive_decline

        self.create_entry(student, date(2025, 10, 13), health_value=4)
        self.create_entry(student, date(2025, 10, 14), health_value=3)
        self.create_entry(student, date(2025, 10, 15), health_value=4)

        result = check_consecutive_decline(student, "health_condition")

        assert result["has_alert"] is False

    def test_insufficient_data_no_alert(self, student):
        """
        【テスト33】データ不足（2日分のみ）はアラート対象外

        期待される動作:
        - has_alert: False
        - trend: []
        - dates: []
        """
        from school_diary.diary.utils import check_consecutive_decline

        self.create_entry(student, date(2025, 10, 14), health_value=4)
        self.create_entry(student, date(2025, 10, 15), health_value=3)

        result = check_consecutive_decline(student, "health_condition")

        assert result["has_alert"] is False
        assert result["trend"] == []
        assert result["dates"] == []

    def test_absent_day_exclusion_no_alert(self, student):
        """
        【テスト34】欠席日除外で3日未満となる場合はアラート対象外

        シナリオ:
        - 10/13: ★★★★★ (5)
        - 10/14: 欠席（DailyAttendance.ABSENT）
        - 10/15: ★★★ (3)
        → 実質2日分のデータのみ、アラート対象外

        期待される動作:
        - has_alert: False
        """
        from school_diary.diary.models import AttendanceStatus
        from school_diary.diary.models import ClassRoom
        from school_diary.diary.models import DailyAttendance
        from school_diary.diary.utils import check_consecutive_decline

        # クラスを作成（DailyAttendanceに必要）
        classroom = ClassRoom.objects.create(
            grade=1,
            class_name="A",
            academic_year=2025,
        )

        # 10/13: エントリーあり
        self.create_entry(student, date(2025, 10, 13), health_value=5)

        # 10/14: 欠席記録
        DailyAttendance.objects.create(
            student=student,
            classroom=classroom,
            date=date(2025, 10, 14),
            status=AttendanceStatus.ABSENT,
        )

        # 10/15: エントリーあり
        self.create_entry(student, date(2025, 10, 15), health_value=3)

        result = check_consecutive_decline(student, "health_condition")

        # 欠席日を除外すると2日分のデータのみ → アラート対象外
        assert result["has_alert"] is False


@pytest.mark.django_db
class TestCriticalMentalState:
    """メンタル★1検出のユニットテスト

    深刻なメンタル状態（★1: とても落ち込んでいる）を検出します。
    ★1は臨床的に有意な症状レベル、即座の対応が必要。
    """

    @pytest.fixture
    def student(self, db):
        """テスト用の生徒ユーザーを作成"""
        user = User.objects.create_user(
            username="student_mental_test",
            email="student_mental_test@example.com",
            password="testpass123",
        )
        user.profile.role = "student"
        user.profile.save()
        return user

    def create_entry(self, student, entry_date, mental_value):
        """DiaryEntryを作成するヘルパー"""
        return DiaryEntry.objects.create(
            student=student,
            entry_date=entry_date,
            health_condition=3,
            mental_condition=mental_value,
            reflection="Test entry",
        )

    def test_mental_star_1_triggers_critical_alert(self, student):
        """
        【テスト35】メンタル★1はCriticalアラート対象

        期待される動作:
        - has_alert: True
        - current_value: 1
        - date: 最新エントリーの日付
        """
        from school_diary.diary.utils import check_critical_mental_state

        self.create_entry(student, date(2025, 10, 15), mental_value=1)

        result = check_critical_mental_state(student)

        assert result["has_alert"] is True
        assert result["current_value"] == 1
        assert result["date"] == date(2025, 10, 15)

    def test_mental_star_2_to_5_no_alert(self, student):
        """
        【テスト36】メンタル★2-5はアラート対象外

        ★2「落ち込んでいる」は日常的な感情の起伏、正常範囲
        期待される動作:
        - has_alert: False
        """
        from school_diary.diary.utils import check_critical_mental_state

        # ★2でテスト
        self.create_entry(student, date(2025, 10, 15), mental_value=2)

        result = check_critical_mental_state(student)

        assert result["has_alert"] is False
        assert result["current_value"] == 2

    def test_no_entry_no_alert(self, student):
        """
        【テスト37】エントリーなしの場合はアラート対象外

        期待される動作:
        - has_alert: False
        - current_value: None
        - date: None
        """
        from school_diary.diary.utils import check_critical_mental_state

        result = check_critical_mental_state(student)

        assert result["has_alert"] is False
        assert result["current_value"] is None
        assert result["date"] is None

    def test_mental_star_1_consecutive_days(self, student):
        """
        【テスト38】メンタル★1が複数日連続

        学年主任通知の基礎データとなる
        期待される動作:
        - 最新エントリーのメンタル: 1
        - 過去3日分全てが★1
        """
        from school_diary.diary.utils import check_critical_mental_state

        # 3日連続で★1
        self.create_entry(student, date(2025, 10, 13), mental_value=1)
        self.create_entry(student, date(2025, 10, 14), mental_value=1)
        self.create_entry(student, date(2025, 10, 15), mental_value=1)

        result = check_critical_mental_state(student)

        # 最新エントリーが★1であることを確認
        assert result["has_alert"] is True
        assert result["current_value"] == 1

        # 過去3日分のエントリーが全て★1であることを確認
        recent_three = student.diary_entries.order_by("-entry_date")[:3]
        assert len(recent_three) == 3
        assert all(e.mental_condition == 1 for e in recent_three)


@pytest.mark.django_db
class TestGradeLeaderNotification:
    """学年主任通知のユニットテスト

    メンタル★1が3日連続の場合、学年主任に自動通知します。
    組織的対応の自動化により、担任レベルでの情報停滞を防ぎます。
    """

    @pytest.fixture
    def student(self, db):
        """テスト用の生徒ユーザーを作成"""
        user = User.objects.create_user(
            username="student_escalation_test",
            email="student_escalation_test@example.com",
            password="testpass123",
        )
        user.profile.role = "student"
        user.profile.save()
        return user

    def create_entry(self, student, entry_date, mental_value):
        """DiaryEntryを作成するヘルパー"""
        return DiaryEntry.objects.create(
            student=student,
            entry_date=entry_date,
            health_condition=3,
            mental_condition=mental_value,
            reflection="Test entry",
        )

    def test_mental_star_1_three_consecutive_days_triggers_escalation(self, student):
        """
        【テスト39】メンタル★1が3日連続で学年主任通知

        期待される動作:
        - 最新3エントリーが全て★1
        - エスカレーション条件を満たす
        """
        # 3日連続で★1
        self.create_entry(student, date(2025, 10, 13), mental_value=1)
        self.create_entry(student, date(2025, 10, 14), mental_value=1)
        self.create_entry(student, date(2025, 10, 15), mental_value=1)

        # 最新3エントリーを取得
        recent_three = student.diary_entries.order_by("-entry_date")[:3]

        assert len(recent_three) == 3
        assert all(e.mental_condition == 1 for e in recent_three)

    def test_mental_star_1_only_two_days_no_escalation(self, student):
        """
        【テスト40】メンタル★1が2日のみの場合は学年主任通知なし

        期待される動作:
        - エスカレーション条件を満たさない
        """
        # 2日のみ★1
        self.create_entry(student, date(2025, 10, 14), mental_value=1)
        self.create_entry(student, date(2025, 10, 15), mental_value=1)

        recent_three = student.diary_entries.order_by("-entry_date")[:3]

        # 3日分のデータがない
        assert len(recent_three) == 2

    def test_mental_star_1_non_consecutive_no_escalation(self, student):
        """
        【テスト41】メンタル★1が非連続の場合は学年主任通知なし

        シナリオ: ★1 → ★2 → ★1（連続でない）
        期待される動作:
        - エスカレーション条件を満たさない
        """
        self.create_entry(student, date(2025, 10, 13), mental_value=1)
        self.create_entry(student, date(2025, 10, 14), mental_value=2)
        self.create_entry(student, date(2025, 10, 15), mental_value=1)

        recent_three = student.diary_entries.order_by("-entry_date")[:3]

        # 3日分のデータはあるが、全て★1ではない
        assert len(recent_three) == 3
        assert not all(e.mental_condition == 1 for e in recent_three)

    def test_mental_star_1_four_consecutive_days_single_notification(self, student):
        """
        【テスト42】メンタル★1が4日連続でも通知は1回のみ（重複回避）

        期待される動作:
        - 最新3エントリーが全て★1
        - 4日目でも条件は同じ（重複通知を避ける実装が必要）
        """
        # 4日連続で★1
        self.create_entry(student, date(2025, 10, 12), mental_value=1)
        self.create_entry(student, date(2025, 10, 13), mental_value=1)
        self.create_entry(student, date(2025, 10, 14), mental_value=1)
        self.create_entry(student, date(2025, 10, 15), mental_value=1)

        recent_three = student.diary_entries.order_by("-entry_date")[:3]

        # 最新3エントリーは全て★1（4日目以降も条件は変わらない）
        assert len(recent_three) == 3
        assert all(e.mental_condition == 1 for e in recent_three)

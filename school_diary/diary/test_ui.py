"""UI Element Tests for Diary App.

このファイルは連絡帳アプリのUI要素が正しく表示されるかをテストします。
ブラウザテストではなく、Django TestClientとBeautifulSoupを使った自動テストです。

実行方法:
    dj pytest school_diary/diary/test_ui.py -v

テスト範囲:
    - DiaryCreateView: フォーム要素の存在確認
    - DiaryHistoryView: テーブル、ページネーション、バッジ表示
"""

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DiaryEntry

User = get_user_model()


@pytest.fixture
def authenticated_client(db):
    """認証済みクライアントを作成するフィクスチャ"""
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
class TestDiaryCreateViewUI:
    """連絡帳作成ページのUI要素テスト

    このテストクラスは、ページ上に必要なUI要素が全て表示されているかを確認します。
    BeautifulSoupを使ってHTMLを解析し、要素の存在、属性、テキスト内容を検証します。
    """

    def test_submit_button_exists(self, authenticated_client):
        """
        【テスト1】送信ボタンが存在する

        期待される動作:
        - type="submit" のボタンが存在する
        - ボタンのテキストに「提出する」が含まれる
        - Bootstrap の btn-primary クラスが適用されている
        """
        # Arrange: URLを取得
        url = reverse("diary:diary_create")

        # Act: ページにアクセス
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert: 送信ボタンが存在し、正しい属性を持つ
        submit_btn = soup.find("button", {"type": "submit"})
        assert submit_btn is not None, (
            "送信ボタン（type='submit'）が見つかりません。"
            "diary_create.html の <form> 内に <button type='submit'> があるか確認してください。"
        )
        assert "提出する" in submit_btn.text, (
            f"送信ボタンのテキストが正しくありません。"
            f"期待: '提出する' を含む、実際: '{submit_btn.text}'"
        )
        assert "btn-primary" in submit_btn.get("class", []), (
            "送信ボタンに btn-primary クラスが適用されていません。"
            "Bootstrap のプライマリボタンスタイルが必要です。"
        )

    def test_cancel_button_exists(self, authenticated_client):
        """
        【テスト2】キャンセルボタンが存在する

        期待される動作:
        - student_dashboard へのリンクが存在する
        - リンクのテキストに「キャンセル」が含まれる
        - Bootstrap の btn-secondary クラスが適用されている
        """
        # Arrange
        url = reverse("diary:diary_create")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        cancel_link = soup.find("a", string=lambda text: text and "キャンセル" in text)
        assert cancel_link is not None, (
            "キャンセルリンクが見つかりません。"
            "diary_create.html に '{% url 'diary:student_dashboard' %}' へのリンクがあるか確認してください。"
        )
        assert cancel_link.get("href") == reverse("diary:student_dashboard"), (
            f"キャンセルリンクのURLが正しくありません。"
            f"期待: {reverse('diary:student_dashboard')}, 実際: {cancel_link.get('href')}"
        )
        assert "btn-secondary" in cancel_link.get("class", []), (
            "キャンセルボタンに btn-secondary クラスが適用されていません。"
        )

    def test_csrf_token_exists(self, authenticated_client):
        """
        【テスト3】CSRFトークンが存在する

        期待される動作:
        - フォーム内に csrfmiddlewaretoken フィールドが存在する
        - セキュリティのため必須
        """
        # Arrange
        url = reverse("diary:diary_create")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
        assert csrf_input is not None, (
            "CSRFトークンが見つかりません。"
            "フォーム内に {% csrf_token %} があるか確認してください。"
        )
        assert csrf_input.get("type") == "hidden", (
            "CSRFトークンは hidden フィールドである必要があります。"
        )

    def test_form_has_post_method(self, authenticated_client):
        """
        【テスト4】フォームのmethodがPOSTである

        期待される動作:
        - <form method="post"> となっている
        - GETではデータを送信できない
        """
        # Arrange
        url = reverse("diary:diary_create")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        form = soup.find("form")
        assert form is not None, (
            "フォームが見つかりません。"
            "diary_create.html に <form> タグがあるか確認してください。"
        )
        assert form.get("method", "").lower() == "post", (
            f"フォームのmethod属性がPOSTではありません。"
            f"実際: '{form.get('method')}'"
        )

    def test_entry_date_field_exists(self, authenticated_client):
        """
        【テスト5】記載日フィールドが存在する

        期待される動作:
        - name="entry_date" のフィールドが存在する
        - type="date" である（日付選択UI）
        """
        # Arrange
        url = reverse("diary:diary_create")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        entry_date_input = soup.find("input", {"name": "entry_date"})
        assert entry_date_input is not None, (
            "記載日フィールド（name='entry_date'）が見つかりません。"
            "DiaryEntryForm の entry_date フィールドが正しくレンダリングされているか確認してください。"
        )
        assert entry_date_input.get("type") == "date", (
            f"記載日フィールドの type が date ではありません。"
            f"実際: '{entry_date_input.get('type')}'"
        )

    def test_health_condition_field_exists(self, authenticated_client):
        """
        【テスト6】体調フィールドが存在する

        期待される動作:
        - name="health_condition" のフィールドが存在する
        - select要素（ドロップダウン）である
        """
        # Arrange
        url = reverse("diary:diary_create")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        health_select = soup.find("select", {"name": "health_condition"})
        assert health_select is not None, (
            "体調フィールド（name='health_condition'）が見つかりません。"
            "DiaryEntryForm の health_condition フィールドが正しくレンダリングされているか確認してください。"
        )
        # 選択肢が5つあることを確認（1〜5）
        options = health_select.find_all("option")
        assert len(options) >= 5, (
            f"体調の選択肢が不足しています。期待: 5以上、実際: {len(options)}"
        )

    def test_mental_condition_field_exists(self, authenticated_client):
        """
        【テスト7】メンタル状態フィールドが存在する

        期待される動作:
        - name="mental_condition" のフィールドが存在する
        - select要素（ドロップダウン）である
        """
        # Arrange
        url = reverse("diary:diary_create")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        mental_select = soup.find("select", {"name": "mental_condition"})
        assert mental_select is not None, (
            "メンタル状態フィールド（name='mental_condition'）が見つかりません。"
            "DiaryEntryForm の mental_condition フィールドが正しくレンダリングされているか確認してください。"
        )
        # 選択肢が5つあることを確認（1〜5）
        options = mental_select.find_all("option")
        assert len(options) >= 5, (
            f"メンタル状態の選択肢が不足しています。期待: 5以上、実際: {len(options)}"
        )

    def test_reflection_field_exists(self, authenticated_client):
        """
        【テスト8】振り返りフィールドが存在する

        期待される動作:
        - name="reflection" のフィールドが存在する
        - textarea要素（複数行テキスト）である
        """
        # Arrange
        url = reverse("diary:diary_create")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        reflection_textarea = soup.find("textarea", {"name": "reflection"})
        assert reflection_textarea is not None, (
            "振り返りフィールド（name='reflection'）が見つかりません。"
            "DiaryEntryForm の reflection フィールドが正しくレンダリングされているか確認してください。"
        )
        # rows属性が5以上であることを確認（十分な入力スペース）
        rows = int(reflection_textarea.get("rows", 0))
        assert rows >= 5, (
            f"振り返りフィールドの rows が不足しています。期待: 5以上、実際: {rows}"
        )

    def test_page_title_correct(self, authenticated_client):
        """
        【テスト9】ページタイトルが正しい

        期待される動作:
        - <title> タグに「連絡帳作成」が含まれる
        - SEOとユーザビリティのため重要
        """
        # Arrange
        url = reverse("diary:diary_create")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        title_tag = soup.find("title")
        assert title_tag is not None, (
            "<title> タグが見つかりません。"
            "base.html または diary_create.html に {% block title %} があるか確認してください。"
        )
        assert "連絡帳作成" in title_tag.text, (
            f"ページタイトルが正しくありません。"
            f"期待: '連絡帳作成' を含む、実際: '{title_tag.text}'"
        )

    def test_section_headings_exist(self, authenticated_client):
        """
        【テスト10】セクション見出しが存在する

        期待される動作:
        - h2 タグに「連絡帳作成」が含まれる
        - ユーザーが今どのページにいるか分かる
        """
        # Arrange
        url = reverse("diary:diary_create")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        h2_tag = soup.find("h2", string=lambda text: text and "連絡帳作成" in text)
        assert h2_tag is not None, (
            "メインヘッダー（<h2>連絡帳作成</h2>）が見つかりません。"
            "diary_create.html のカードヘッダーに適切な見出しがあるか確認してください。"
        )


@pytest.fixture
def authenticated_client_with_entries(db):
    """認証済みクライアント + テストデータを作成するフィクスチャ"""
    user = User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )

    # テストデータを3件作成
    for i in range(3):
        DiaryEntry.objects.create(
            student=user,
            entry_date=timezone.now().date() - timezone.timedelta(days=i),
            health_condition=3,  # 普通
            mental_condition=4,  # 元気
            reflection=f"テスト日記{i+1}",
        )

    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
class TestDiaryHistoryViewUI:
    """過去記録閲覧ページのUI要素テスト

    このテストクラスは、過去記録一覧ページのUI要素が正しく表示されているかを確認します。
    """

    def test_page_title_correct(self, authenticated_client):
        """
        【テスト1】ページタイトルが正しい

        期待される動作:
        - <title> タグに「過去の記録」が含まれる
        """
        # Arrange
        url = reverse("diary:diary_history")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        title_tag = soup.find("title")
        assert title_tag is not None, (
            "<title> タグが見つかりません。"
        )
        assert "過去の記録" in title_tag.text, (
            f"ページタイトルが正しくありません。"
            f"期待: '過去の記録' を含む、実際: '{title_tag.text}'"
        )

    def test_back_button_exists(self, authenticated_client):
        """
        【テスト2】ダッシュボードに戻るボタンが存在する

        期待される動作:
        - student_dashboard へのリンクが存在する
        - リンクのテキストに「ダッシュボードに戻る」が含まれる
        """
        # Arrange
        url = reverse("diary:diary_history")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        back_link = soup.find("a", string=lambda text: text and "ダッシュボードに戻る" in text)
        assert back_link is not None, (
            "「ダッシュボードに戻る」リンクが見つかりません。"
            "diary_history.html にダッシュボードへのリンクがあるか確認してください。"
        )
        assert back_link.get("href") == reverse("diary:student_dashboard"), (
            f"戻るリンクのURLが正しくありません。"
            f"期待: {reverse('diary:student_dashboard')}, 実際: {back_link.get('href')}"
        )

    def test_no_data_message_displayed(self, authenticated_client):
        """
        【テスト3】データがない場合のメッセージが表示される

        期待される動作:
        - 連絡帳がない場合、「まだ連絡帳を提出していません」が表示される
        """
        # Arrange
        url = reverse("diary:diary_history")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        alert = soup.find("div", class_="alert-info")
        assert alert is not None, (
            "データなしメッセージ（alert-info）が見つかりません。"
        )
        assert "まだ連絡帳を提出していません" in alert.text, (
            f"メッセージ内容が正しくありません。実際: '{alert.text}'"
        )

    def test_table_exists_with_data(self, authenticated_client_with_entries):
        """
        【テスト4】データがある場合、テーブルが表示される

        期待される動作:
        - table 要素が存在する
        - table-striped と table-hover クラスが適用されている
        """
        # Arrange
        url = reverse("diary:diary_history")

        # Act
        response = authenticated_client_with_entries.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        table = soup.find("table")
        assert table is not None, (
            "テーブルが見つかりません。"
            "diary_history.html に <table> 要素があるか確認してください。"
        )
        table_classes = table.get("class", [])
        assert "table-striped" in table_classes, (
            "table-striped クラスが適用されていません。"
        )
        assert "table-hover" in table_classes, (
            "table-hover クラスが適用されていません。"
        )

    def test_table_headers_correct(self, authenticated_client_with_entries):
        """
        【テスト5】テーブルヘッダーが正しい

        期待される動作:
        - 「日付」「体調」「メンタル」「既読状態」のヘッダーが存在する
        """
        # Arrange
        url = reverse("diary:diary_history")

        # Act
        response = authenticated_client_with_entries.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        thead = soup.find("thead")
        assert thead is not None, (
            "<thead> が見つかりません。"
        )
        headers = [th.text.strip() for th in thead.find_all("th")]
        expected_headers = ["日付", "体調", "メンタル", "既読状態"]

        for expected in expected_headers:
            assert expected in headers, (
                f"ヘッダー '{expected}' が見つかりません。実際のヘッダー: {headers}"
            )

    def test_entry_displayed_with_badges(self, authenticated_client_with_entries):
        """
        【テスト6】連絡帳がバッジ付きで表示される

        期待される動作:
        - tbody に tr 要素が存在する
        - バッジ（badge クラス）が表示される
        """
        # Arrange
        url = reverse("diary:diary_history")

        # Act
        response = authenticated_client_with_entries.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        tbody = soup.find("tbody")
        assert tbody is not None, (
            "<tbody> が見つかりません。"
        )

        rows = tbody.find_all("tr")
        assert len(rows) >= 1, (
            "データ行が見つかりません。テストデータが正しく表示されていない可能性があります。"
        )

        # バッジの存在確認
        badges = tbody.find_all("span", class_="badge")
        assert len(badges) >= 3, (  # 体調、メンタル、既読状態の3つ以上
            f"バッジが不足しています。期待: 3以上、実際: {len(badges)}"
        )

    def test_pagination_elements_exist_with_many_entries(self, authenticated_client):
        """
        【テスト7】ページネーション要素が表示される（11件以上のデータ）

        期待される動作:
        - 11件以上のデータがある場合、ページネーション（pagination）が表示される
        """
        # Arrange: 11件のデータを作成（paginate_by=10 なので2ページになる）
        user = User.objects.get(username="testuser")
        for i in range(11):
            DiaryEntry.objects.create(
                student=user,
                entry_date=timezone.now().date() - timezone.timedelta(days=i),
                health_condition=3,
                mental_condition=3,
                reflection=f"テスト日記{i+1}",
            )

        url = reverse("diary:diary_history")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        pagination = soup.find("ul", class_="pagination")
        assert pagination is not None, (
            "ページネーション（<ul class='pagination'>）が見つかりません。"
            "11件以上のデータでページネーションが表示されるか確認してください。"
        )


@pytest.mark.django_db
class TestRootURLRedirect:
    """ルートURL（/）のリダイレクトテスト

    ルートURLにアクセスした際に、認証状態と役割に応じて適切にリダイレクトされることを確認します。
    """

    def test_root_url_redirects_to_login_when_unauthenticated(self):
        """
        【テスト1】未認証ユーザーがルートURLにアクセスするとログインページにリダイレクト

        期待される動作:
        - / にアクセスすると HTTP 302 (Found) が返る
        - Location ヘッダーが /accounts/login/ を指している
        """
        # Arrange: 未認証クライアントを作成
        client = Client()

        # Act: ルートURLにアクセス
        response = client.get("/", follow=False)

        # Assert: リダイレクトが発生する
        assert response.status_code == 302, (
            f"ルートURLのステータスコードが302ではありません。"
            f"実際: {response.status_code}"
        )
        assert response.url == "/accounts/login/", (
            f"リダイレクト先が正しくありません。"
            f"期待: /accounts/login/, 実際: {response.url}"
        )

    def test_root_url_redirects_to_admin_for_staff(self):
        """
        【テスト2】管理者がルートURLにアクセスすると管理画面にリダイレクト

        期待される動作:
        - / にアクセスすると HTTP 302 (Found) が返る
        - Location ヘッダーが /admin/ を指している
        """
        # Arrange: 管理者ユーザーを作成
        admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="admin123",
            is_staff=True,
        )
        client = Client()
        client.force_login(admin_user)

        # Act: ルートURLにアクセス
        response = client.get("/", follow=False)

        # Assert: 管理画面にリダイレクト
        assert response.status_code == 302, (
            f"ステータスコードが302ではありません。実際: {response.status_code}"
        )
        assert response.url == "/admin/", (
            f"リダイレクト先が正しくありません。期待: /admin/, 実際: {response.url}"
        )

    def test_root_url_redirects_to_student_dashboard(self):
        """
        【テスト3】生徒がルートURLにアクセスすると生徒ダッシュボードにリダイレクト

        期待される動作:
        - / にアクセスすると HTTP 302 (Found) が返る
        - Location ヘッダーが /diary/dashboard/ を指している
        """
        # Arrange: 生徒ユーザーを作成
        student_user = User.objects.create_user(
            username="student",
            email="student@example.com",
            password="student123",
        )
        client = Client()
        client.force_login(student_user)

        # Act: ルートURLにアクセス
        response = client.get("/", follow=False)

        # Assert: 生徒ダッシュボードにリダイレクト
        assert response.status_code == 302, (
            f"ステータスコードが302ではありません。実際: {response.status_code}"
        )
        from django.urls import reverse
        expected_url = reverse("diary:student_dashboard")
        assert response.url == expected_url, (
            f"リダイレクト先が正しくありません。期待: {expected_url}, 実際: {response.url}"
        )


@pytest.fixture
def teacher_client_with_class(db):
    """担任ユーザー + クラス + 生徒 + 連絡帳データを作成するフィクスチャ"""
    # 担任ユーザー作成
    teacher = User.objects.create_user(
        username="teacher",
        email="teacher@example.com",
        password="teacher123",
        is_staff=False,
    )

    # クラス作成
    classroom = ClassRoom.objects.create(
        grade=1,
        class_name="A",
        academic_year=2025,
        homeroom_teacher=teacher,
    )

    # 生徒作成
    student1 = User.objects.create_user(
        username="student1",
        first_name="太郎",
        last_name="山田",
        email="student1@example.com",
    )
    student2 = User.objects.create_user(
        username="student2",
        first_name="花子",
        last_name="佐藤",
        email="student2@example.com",
    )
    classroom.students.add(student1, student2)

    # 連絡帳作成（student1: 未読1件、student2: 既読1件）
    DiaryEntry.objects.create(
        student=student1,
        entry_date=timezone.now().date(),
        health_condition=4,
        mental_condition=5,
        reflection="元気です",
        is_read=False,
    )

    DiaryEntry.objects.create(
        student=student2,
        entry_date=timezone.now().date(),
        health_condition=3,
        mental_condition=3,
        reflection="普通です",
        is_read=True,
        read_by=teacher,
        read_at=timezone.now(),
    )

    client = Client()
    client.force_login(teacher)
    return client


@pytest.mark.django_db
class TestTeacherDashboardViewUI:
    """担任ダッシュボードページのUI要素テスト

    このテストクラスは、担任ダッシュボードのUI要素が正しく表示されているかを確認します。
    """

    def test_page_title_correct(self, teacher_client_with_class):
        """
        【テスト1】ページタイトルが正しい

        期待される動作:
        - <title> タグに「担任ダッシュボード」が含まれる
        """
        # Arrange
        url = reverse("diary:teacher_dashboard")

        # Act
        response = teacher_client_with_class.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        title_tag = soup.find("title")
        assert title_tag is not None, "<title> タグが見つかりません。"
        assert "担任ダッシュボード" in title_tag.text, (
            f"ページタイトルが正しくありません。"
            f"期待: '担任ダッシュボード' を含む、実際: '{title_tag.text}'"
        )

    def test_classroom_info_displayed(self, teacher_client_with_class):
        """
        【テスト2】クラス情報が表示される

        期待される動作:
        - クラス名（2025年度 1年A組）が表示される
        - 生徒数が表示される
        """
        # Arrange
        url = reverse("diary:teacher_dashboard")

        # Act
        response = teacher_client_with_class.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        lead = soup.find("p", class_="lead")
        assert lead is not None, "<p class='lead'> が見つかりません。"
        assert "2025年度 1年A組" in lead.text, (
            f"クラス情報が正しく表示されていません。実際: '{lead.text}'"
        )
        assert "2名" in lead.text, (
            f"生徒数が正しく表示されていません。実際: '{lead.text}'"
        )

    def test_student_table_exists(self, teacher_client_with_class):
        """
        【テスト3】生徒一覧テーブルが存在する

        期待される動作:
        - table 要素が存在する
        - table-hover クラスが適用されている
        """
        # Arrange
        url = reverse("diary:teacher_dashboard")

        # Act
        response = teacher_client_with_class.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        table = soup.find("table")
        assert table is not None, "テーブルが見つかりません。"
        table_classes = table.get("class", [])
        assert "table-hover" in table_classes, (
            "table-hover クラスが適用されていません。"
        )

    def test_table_headers_correct(self, teacher_client_with_class):
        """
        【テスト4】テーブルヘッダーが正しい

        期待される動作:
        - 「生徒名」「体調」「メンタル」「対応状況」のヘッダーが存在する
        """
        # Arrange
        url = reverse("diary:teacher_dashboard")

        # Act
        response = teacher_client_with_class.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        thead = soup.find("thead")
        assert thead is not None, "<thead> が見つかりません。"
        headers = [th.text.strip() for th in thead.find_all("th")]
        expected_headers = ["生徒名", "体調", "メンタル", "対応状況"]

        for expected in expected_headers:
            assert expected in headers, (
                f"ヘッダー '{expected}' が見つかりません。実際のヘッダー: {headers}"
            )

    def test_unread_badge_displayed(self, teacher_client_with_class):
        """
        【テスト5】未読バッジが表示される

        期待される動作:
        - 未読がある生徒に 🔵 NEW バッジ（bg-info）が表示される
        """
        # Arrange
        url = reverse("diary:teacher_dashboard")

        # Act
        response = teacher_client_with_class.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        tbody = soup.find("tbody")
        assert tbody is not None, "<tbody> が見つかりません。"

        # 未読バッジ（bg-info）の確認
        info_badge = tbody.find(
            "span",
            class_=lambda x: x and "bg-info" in x,
        )
        assert info_badge is not None, (
            "未読バッジ（bg-info）が見つかりません。"
        )
        assert "NEW" in info_badge.text, (
            f"未読バッジのテキストが正しく表示されていません。実際: '{info_badge.text}'"
        )

    def test_student_health_mental_displayed(self, teacher_client_with_class):
        """
        【テスト6】生徒の体調・メンタルが表示される

        期待される動作:
        - 最新の体調が絵文字バッジで表示される（🟢🟡🔴）
        - 最新のメンタルが絵文字バッジで表示される（🟢🟡🔴）
        """
        # Arrange
        url = reverse("diary:teacher_dashboard")

        # Act
        response = teacher_client_with_class.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        tbody = soup.find("tbody")
        assert tbody is not None, "<tbody> が見つかりません。"

        # 体調・メンタルのバッジ（badge）が表示されていることを確認
        badges = tbody.find_all("span", class_="badge")
        assert len(badges) >= 2, (
            f"体調・メンタルバッジが不足しています。期待: 2以上、実際: {len(badges)}"
        )

    def test_no_classroom_alert_displayed(self, authenticated_client):
        """
        【テスト7】担当クラスがない場合、アラートが表示される

        期待される動作:
        - 担当クラスがない場合、alert-info が表示される
        - 「担当クラスがありません」メッセージが含まれる
        """
        # Arrange
        url = reverse("diary:teacher_dashboard")

        # Act
        response = authenticated_client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        alert = soup.find("div", class_="alert-info")
        assert alert is not None, (
            "アラート（alert-info）が見つかりません。"
        )
        assert "担当クラスがありません" in alert.text, (
            f"メッセージ内容が正しくありません。実際: '{alert.text}'"
        )


@pytest.fixture
def teacher_with_student_entry(db):
    """担任 + 生徒 + クラス + 未読連絡帳のフィクスチャ

    反応・対応記録フロー検証用のテストデータセット
    """
    from datetime import date, timedelta

    # 担任ユーザー作成
    teacher = User.objects.create_user(
        username="teacher_test",
        email="teacher_test@example.com",
        password="teacher123",
        first_name="太郎",
        last_name="先生",
        is_staff=False,
    )

    # 生徒ユーザー作成
    student = User.objects.create_user(
        username="student_test",
        email="student_test@example.com",
        password="student123",
        first_name="花子",
        last_name="生徒",
    )

    # クラス作成
    classroom = ClassRoom.objects.create(
        grade=1,
        class_name="A",
        academic_year=2025,
        homeroom_teacher=teacher,
    )
    classroom.students.add(student)

    # 未読連絡帳作成
    entry = DiaryEntry.objects.create(
        student=student,
        entry_date=date.today() - timedelta(days=1),
        health_condition=4,
        mental_condition=4,
        reflection="テスト用の振り返り内容です。",
        is_read=False,
    )

    # 認証済みクライアント
    client = Client()
    client.force_login(teacher)

    return {
        "client": client,
        "teacher": teacher,
        "student": student,
        "classroom": classroom,
        "entry": entry,
    }


@pytest.mark.django_db
class TestTeacherReactionAndActionFlow:
    """担任の反応・対応記録フローの完全テスト

    このテストクラスは、担任が生徒の連絡帳に対して：
    1. 反応（public_reaction）を追加/変更できる
    2. 対応記録（internal_action）を追加/変更/削除できる
    3. 既読処理と独立して反応・対応を編集できる

    という完全なフローを検証します。
    """

    def test_mark_as_read_with_reaction_only(self, teacher_with_student_entry):
        """
        【テスト1】未読→既読（反応のみ）

        期待される動作:
        - 未読の連絡帳に対して反応を選択して既読にできる
        - internal_actionは空（NULL）のまま
        - is_read, read_by, read_atが設定される
        """
        # Arrange
        data = teacher_with_student_entry
        entry = data["entry"]
        url = reverse("diary:teacher_mark_as_read", args=[entry.id])

        # Act
        response = data["client"].post(url, {"public_reaction": "checked"})

        # Assert
        assert response.status_code == 302, (
            f"リダイレクトが発生しませんでした。ステータス: {response.status_code}"
        )

        entry.refresh_from_db()
        assert entry.is_read is True, "既読フラグが立っていません。"
        assert entry.public_reaction == "checked", (
            f"反応が保存されていません。期待: 'checked', 実際: {entry.public_reaction}"
        )
        assert entry.internal_action is None, (
            "internal_actionは空であるべきです。"
        )
        assert entry.read_by == data["teacher"], "read_byが正しく設定されていません。"
        assert entry.read_at is not None, "read_atが設定されていません。"

    def test_mark_as_read_with_reaction_and_action(self, teacher_with_student_entry):
        """
        【テスト2】未読→既読（反応+対応記録）

        期待される動作:
        - 反応と対応記録を同時に設定して既読にできる
        - action_statusがpendingになる
        """
        # Arrange
        data = teacher_with_student_entry
        entry = data["entry"]
        url = reverse("diary:teacher_mark_as_read", args=[entry.id])

        # Act
        response = data["client"].post(url, {
            "public_reaction": "thumbs_up",
            "internal_action": "needs_follow_up",
        })

        # Assert
        assert response.status_code == 302

        entry.refresh_from_db()
        assert entry.is_read is True
        assert entry.public_reaction == "thumbs_up"
        assert entry.internal_action == "needs_follow_up"
        from school_diary.diary.models import ActionStatus
        assert entry.action_status == ActionStatus.PENDING, (
            "action_statusがpendingになっていません。"
        )

    def test_update_reaction_after_read(self, teacher_with_student_entry):
        """
        【テスト3】既読済みの連絡帳に反応を追加

        期待される動作:
        - 既読済みの連絡帳に対して、後から反応を追加できる
        - 既読状態は変わらない

        ⚠️ 現在の実装では失敗する（未実装機能）
        """
        # Arrange
        data = teacher_with_student_entry
        entry = data["entry"]

        # まず既読にする（反応なし）
        entry.is_read = True
        entry.read_by = data["teacher"]
        entry.read_at = timezone.now()
        entry.save()

        url = reverse("diary:teacher_mark_as_read", args=[entry.id])

        # Act: 後から反応を追加
        response = data["client"].post(url, {"public_reaction": "thumbs_up"})

        # Assert
        assert response.status_code == 302

        entry.refresh_from_db()
        assert entry.public_reaction == "thumbs_up", (
            "既読済みの連絡帳に反応を追加できていません。"
        )

    def test_update_action_after_read(self, teacher_with_student_entry):
        """
        【テスト4】既読済みの連絡帳に対応記録を追加

        期待される動作:
        - 既読済みの連絡帳に対して、後から対応記録を追加できる
        - action_statusがpendingになる

        ⚠️ 現在の実装では失敗する（未実装機能）
        """
        # Arrange
        data = teacher_with_student_entry
        entry = data["entry"]

        # まず既読にする（対応記録なし）
        entry.is_read = True
        entry.read_by = data["teacher"]
        entry.read_at = timezone.now()
        entry.save()

        url = reverse("diary:teacher_mark_as_read", args=[entry.id])

        # Act: 後から対応記録を追加
        response = data["client"].post(url, {"internal_action": "needs_follow_up"})

        # Assert
        assert response.status_code == 302

        entry.refresh_from_db()
        assert entry.internal_action == "needs_follow_up", (
            "既読済みの連絡帳に対応記録を追加できていません。"
        )
        from school_diary.diary.models import ActionStatus
        assert entry.action_status == ActionStatus.PENDING

    def test_change_reaction_after_read(self, teacher_with_student_entry):
        """
        【テスト5】既読済みの連絡帳の反応を変更

        期待される動作:
        - 既に設定されている反応を変更できる

        ⚠️ 現在の実装では失敗する（未実装機能）
        """
        # Arrange
        data = teacher_with_student_entry
        entry = data["entry"]

        # 既読にして反応を設定
        entry.is_read = True
        entry.read_by = data["teacher"]
        entry.read_at = timezone.now()
        entry.public_reaction = "checked"
        entry.save()

        url = reverse("diary:teacher_mark_as_read", args=[entry.id])

        # Act: 反応を変更
        response = data["client"].post(url, {"public_reaction": "excellent"})

        # Assert
        assert response.status_code == 302

        entry.refresh_from_db()
        assert entry.public_reaction == "excellent", (
            f"反応を変更できていません。期待: 'excellent', 実際: {entry.public_reaction}"
        )

    def test_change_action_after_read(self, teacher_with_student_entry):
        """
        【テスト6】既読済みの連絡帳の対応記録を変更

        期待される動作:
        - 既に設定されている対応記録を変更できる
        - action_statusがpendingにリセットされる（対応完了→未対応に戻る）

        ⚠️ 現在の実装では失敗する（未実装機能）
        """
        # Arrange
        data = teacher_with_student_entry
        entry = data["entry"]

        # 既読にして対応記録を設定（完了済み）
        entry.is_read = True
        entry.read_by = data["teacher"]
        entry.read_at = timezone.now()
        entry.internal_action = "monitoring"
        from school_diary.diary.models import ActionStatus
        entry.action_status = ActionStatus.COMPLETED
        entry.action_completed_by = data["teacher"]
        entry.action_completed_at = timezone.now()
        entry.save()

        url = reverse("diary:teacher_mark_as_read", args=[entry.id])

        # Act: 対応記録を変更（緊急対応必要に変更）
        response = data["client"].post(url, {"internal_action": "urgent"})

        # Assert
        assert response.status_code == 302

        entry.refresh_from_db()
        assert entry.internal_action == "urgent"
        assert entry.action_status == ActionStatus.PENDING, (
            "対応記録を変更したら、action_statusがpendingにリセットされるべきです。"
        )

    def test_remove_action_after_read(self, teacher_with_student_entry):
        """
        【テスト7】既読済みの連絡帳の対応記録を削除

        期待される動作:
        - 既に設定されている対応記録を削除できる（空文字列を送信）
        - action_statusはNOT_REQUIREDになる（models.pyの自動設定）

        Note: 対応記録を削除すると、models.pyのsave()メソッドが自動的に
        action_statusをNOT_REQUIREDに設定します。これは「対応不要と判断した」
        という履歴を残すため、NULLではなくNOT_REQUIREDにする方が望ましいです。
        """
        # Arrange
        data = teacher_with_student_entry
        entry = data["entry"]

        # 既読にして対応記録を設定
        entry.is_read = True
        entry.read_by = data["teacher"]
        entry.read_at = timezone.now()
        entry.internal_action = "needs_follow_up"
        from school_diary.diary.models import ActionStatus
        entry.action_status = ActionStatus.PENDING
        entry.save()

        url = reverse("diary:teacher_mark_as_read", args=[entry.id])

        # Act: 対応記録を削除（空文字列を送信）
        response = data["client"].post(url, {"internal_action": ""})

        # Assert
        assert response.status_code == 302

        entry.refresh_from_db()
        assert entry.internal_action is None, (
            "対応記録を削除できていません。"
        )
        assert entry.action_status == ActionStatus.NOT_REQUIRED, (
            "対応記録を削除したら、action_statusがNOT_REQUIREDになるべきです。"
        )

    def test_action_status_management(self, teacher_with_student_entry):
        """
        【テスト8】action_statusの管理

        期待される動作:
        - internal_actionを設定 → action_status = PENDING
        - action_completedを実行 → action_status = COMPLETED
        - internal_actionを削除 → action_status = NOT_REQUIRED

        Note: 完全なライフサイクルを検証します。対応記録を削除すると、
        models.pyの自動設定によりaction_statusがNOT_REQUIREDになります。
        """
        # Arrange
        data = teacher_with_student_entry
        entry = data["entry"]
        url = reverse("diary:teacher_mark_as_read", args=[entry.id])

        # Act 1: 対応記録を設定
        data["client"].post(url, {"internal_action": "needs_follow_up"})
        entry.refresh_from_db()

        from school_diary.diary.models import ActionStatus
        assert entry.action_status == ActionStatus.PENDING, (
            "対応記録を設定したら、action_statusがpendingになるべきです。"
        )

        # Act 2: 対応完了
        complete_url = reverse("diary:teacher_mark_action_completed", args=[entry.id])
        data["client"].post(complete_url, {"action_note": "面談実施"})
        entry.refresh_from_db()

        assert entry.action_status == ActionStatus.COMPLETED, (
            "対応完了処理後、action_statusがcompletedになるべきです。"
        )

        # Act 3: 対応記録を削除
        data["client"].post(url, {"internal_action": ""})
        entry.refresh_from_db()

        assert entry.internal_action is None, (
            "対応記録を削除できていません。"
        )
        assert entry.action_status == ActionStatus.NOT_REQUIRED, (
            "対応記録を削除したら、action_statusがNOT_REQUIREDになるべきです。"
        )


@pytest.fixture
def teacher_with_notes_data(db):
    """担任メモ機能テスト用フィクスチャ

    担任2名、生徒1名、担任メモ（共有・非共有）を作成
    """
    from school_diary.diary.models import TeacherNote

    # 担任1（テストユーザー）
    teacher1 = User.objects.create_user(
        username="teacher1",
        email="teacher1@example.com",
        password="teacher123",
        first_name="太郎",
        last_name="先生",
        is_staff=False,
    )

    # 担任2（同じ学年）
    teacher2 = User.objects.create_user(
        username="teacher2",
        email="teacher2@example.com",
        password="teacher123",
        first_name="次郎",
        last_name="先生",
        is_staff=False,
    )

    # 生徒
    student = User.objects.create_user(
        username="student_notes",
        email="student_notes@example.com",
        first_name="花子",
        last_name="山田",
    )

    # クラス作成（teacher1が担任）
    classroom = ClassRoom.objects.create(
        grade=1,
        class_name="A",
        academic_year=2025,
        homeroom_teacher=teacher1,
    )
    classroom.students.add(student)

    # 担任メモ作成
    # 1. teacher1の個人メモ（非共有）
    note1 = TeacherNote.objects.create(
        teacher=teacher1,
        student=student,
        note="個人メモ：家庭環境について配慮が必要。母子家庭で夜遅くまで母親不在。",
        is_shared=False,
    )

    # 2. teacher1の共有メモ
    note2 = TeacherNote.objects.create(
        teacher=teacher1,
        student=student,
        note="共有メモ：体調不良が続く場合は保護者に連絡してください。",
        is_shared=True,
    )

    # 3. teacher2の共有メモ
    note3 = TeacherNote.objects.create(
        teacher=teacher2,
        student=student,
        note="共有メモ（teacher2）：学年会議で共有された情報です。",
        is_shared=True,
    )

    # 認証済みクライアント（teacher1としてログイン）
    client = Client()
    client.force_login(teacher1)

    return {
        "client": client,
        "teacher1": teacher1,
        "teacher2": teacher2,
        "student": student,
        "classroom": classroom,
        "note1": note1,  # teacher1の個人メモ
        "note2": note2,  # teacher1の共有メモ
        "note3": note3,  # teacher2の共有メモ
    }


@pytest.mark.django_db
class TestTeacherNotesUI:
    """担任メモ機能のUI要素テスト

    このテストクラスは、担任メモ機能のUI要素が正しく表示され、
    権限管理が適切に動作することを確認します。
    """

    def test_notes_section_exists(self, teacher_with_notes_data):
        """
        【テスト1】担任メモセクションが表示される

        期待される動作:
        - teacher_student_detail ページに担任メモセクションが存在する
        - セクションヘッダーに「担任メモ」が含まれる
        """
        # Arrange
        data = teacher_with_notes_data
        url = reverse("diary:teacher_student_detail", args=[data["student"].id])

        # Act
        response = data["client"].get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        header = soup.find("h5", string=lambda text: text and "担任メモ" in text)
        assert header is not None, (
            "担任メモセクションのヘッダーが見つかりません。"
            "teacher_student_detail.html に担任メモセクションがあるか確認してください。"
        )

    def test_add_note_button_exists(self, teacher_with_notes_data):
        """
        【テスト2】新規メモ追加ボタンが存在する

        期待される動作:
        - 「新規メモ追加」ボタンが存在する
        - ボタンをクリックするとモーダルが開く（data-bs-toggle="modal"）
        """
        # Arrange
        data = teacher_with_notes_data
        url = reverse("diary:teacher_student_detail", args=[data["student"].id])

        # Act
        response = data["client"].get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        add_button = soup.find("button", string=lambda text: text and "新規メモ追加" in text)
        assert add_button is not None, (
            "「新規メモ追加」ボタンが見つかりません。"
        )
        assert add_button.get("data-bs-toggle") == "modal", (
            "新規メモ追加ボタンにdata-bs-toggle='modal'が設定されていません。"
        )

    def test_notes_displayed_with_correct_badges(self, teacher_with_notes_data):
        """
        【テスト3】担任メモが正しいバッジ付きで表示される

        期待される動作:
        - 共有メモには「👥 学年共有」バッジ（bg-primary）が表示される
        - 個人メモには「🔒 個人メモ」バッジ（bg-secondary）が表示される
        """
        # Arrange
        data = teacher_with_notes_data
        url = reverse("diary:teacher_student_detail", args=[data["student"].id])

        # Act
        response = data["client"].get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        # 共有メモバッジの確認
        shared_badge = soup.find("span", string=lambda text: text and "学年共有" in text)
        assert shared_badge is not None, (
            "共有メモバッジ（学年共有）が見つかりません。"
        )
        assert "bg-primary" in shared_badge.get("class", []), (
            "共有メモバッジにbg-primaryクラスが適用されていません。"
        )

        # 個人メモバッジの確認
        private_badge = soup.find("span", string=lambda text: text and "個人メモ" in text)
        assert private_badge is not None, (
            "個人メモバッジ（個人メモ）が見つかりません。"
        )
        assert "bg-secondary" in private_badge.get("class", []), (
            "個人メモバッジにbg-secondaryクラスが適用されていません。"
        )

    def test_edit_delete_buttons_only_for_creator(self, teacher_with_notes_data):
        """
        【テスト4】編集・削除ボタンは作成者のみに表示される

        期待される動作:
        - teacher1のメモ（note1, note2）には編集・削除ボタンが表示される
        - teacher2のメモ（note3）には編集・削除ボタンが表示されない
        """
        # Arrange
        data = teacher_with_notes_data
        url = reverse("diary:teacher_student_detail", args=[data["student"].id])

        # Act
        response = data["client"].get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        # 編集モーダルの確認（teacher1のメモ用のモーダルは存在）
        edit_modal1 = soup.find("div", id=f"editNoteModal{data['note1'].id}")
        assert edit_modal1 is not None, (
            "teacher1のメモ用の編集モーダルが見つかりません。"
        )

        edit_modal2 = soup.find("div", id=f"editNoteModal{data['note2'].id}")
        assert edit_modal2 is not None, (
            "teacher1の共有メモ用の編集モーダルが見つかりません。"
        )

        # teacher2のメモ用の編集モーダルは存在しない
        edit_modal3 = soup.find("div", id=f"editNoteModal{data['note3'].id}")
        assert edit_modal3 is None, (
            "teacher2のメモ用の編集モーダルが表示されていますが、表示されるべきではありません。"
        )

    def test_shared_notes_visible_to_other_teachers(self, teacher_with_notes_data):
        """
        【テスト5】共有メモは他の担任にも表示される

        期待される動作:
        - teacher2の共有メモ（note3）が表示される
        - teacher1の個人メモ（note1）も表示される（自分のメモだから）
        """
        # Arrange
        data = teacher_with_notes_data
        url = reverse("diary:teacher_student_detail", args=[data["student"].id])

        # Act
        response = data["client"].get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        # note2（teacher1の共有メモ）が表示されている
        note2_content = soup.find(string=lambda text: text and "体調不良が続く" in text)
        assert note2_content is not None, (
            "teacher1の共有メモが表示されていません。"
        )

        # note3（teacher2の共有メモ）が表示されている
        note3_content = soup.find(string=lambda text: text and "学年会議で共有" in text)
        assert note3_content is not None, (
            "teacher2の共有メモが表示されていません。"
        )

    def test_add_note_modal_structure(self, teacher_with_notes_data):
        """
        【テスト6】新規メモ追加モーダルの構造が正しい

        期待される動作:
        - モーダルに note フィールド（textarea）が存在する
        - is_shared チェックボックスが存在する
        - フォームのactionが teacher_add_note URLになっている
        """
        # Arrange
        data = teacher_with_notes_data
        url = reverse("diary:teacher_student_detail", args=[data["student"].id])

        # Act
        response = data["client"].get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        add_modal = soup.find("div", id="addNoteModal")
        assert add_modal is not None, (
            "新規メモ追加モーダル（id='addNoteModal'）が見つかりません。"
        )

        # テキストエリアの確認
        note_textarea = add_modal.find("textarea", {"name": "note"})
        assert note_textarea is not None, (
            "メモ内容のテキストエリア（name='note'）が見つかりません。"
        )

        # 共有チェックボックスの確認
        shared_checkbox = add_modal.find("input", {"name": "is_shared", "type": "checkbox"})
        assert shared_checkbox is not None, (
            "共有チェックボックス（name='is_shared'）が見つかりません。"
        )

        # フォームのactionURL確認
        form = add_modal.find("form")
        assert form is not None, (
            "新規メモ追加モーダル内にformが見つかりません。"
        )
        expected_url = reverse("diary:teacher_add_note", args=[data["student"].id])
        assert form.get("action") == expected_url, (
            f"フォームのaction URLが正しくありません。"
            f"期待: {expected_url}, 実際: {form.get('action')}"
        )

    def test_edit_note_modal_preloaded(self, teacher_with_notes_data):
        """
        【テスト7】編集モーダルに既存メモ内容がプリロードされている

        期待される動作:
        - 編集モーダルのテキストエリアに既存のメモ内容が表示される
        - 共有チェックボックスが既存の状態を反映している
        """
        # Arrange
        data = teacher_with_notes_data
        url = reverse("diary:teacher_student_detail", args=[data["student"].id])

        # Act
        response = data["client"].get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        edit_modal = soup.find("div", id=f"editNoteModal{data['note2'].id}")
        assert edit_modal is not None, (
            "編集モーダルが見つかりません。"
        )

        # テキストエリアに既存内容が含まれている
        note_textarea = edit_modal.find("textarea", {"name": "note"})
        assert note_textarea is not None, (
            "編集モーダル内のテキストエリアが見つかりません。"
        )
        assert data["note2"].note in note_textarea.text, (
            "編集モーダルのテキストエリアに既存のメモ内容が表示されていません。"
        )

        # 共有チェックボックスがチェックされている（note2はis_shared=True）
        shared_checkbox = edit_modal.find("input", {"name": "is_shared"})
        assert shared_checkbox is not None, (
            "編集モーダル内の共有チェックボックスが見つかりません。"
        )
        assert shared_checkbox.has_attr("checked"), (
            "共有メモの編集モーダルで、共有チェックボックスがチェックされていません。"
        )

    def test_no_notes_message_displayed(self, authenticated_client):
        """
        【テスト8】担任メモがない場合のメッセージ表示

        期待される動作:
        - 担任メモがない生徒の詳細ページでは「担任メモはまだありません」メッセージが表示される
        """
        # Arrange: メモがない生徒を作成
        student = User.objects.create_user(
            username="student_no_notes",
            email="no_notes@example.com",
            first_name="次郎",
            last_name="佐藤",
        )
        teacher = User.objects.create_user(
            username="teacher_no_notes",
            email="teacher_no_notes@example.com",
            is_staff=False,
        )
        classroom = ClassRoom.objects.create(
            grade=1,
            class_name="B",
            academic_year=2025,
            homeroom_teacher=teacher,
        )
        classroom.students.add(student)

        client = Client()
        client.force_login(teacher)

        url = reverse("diary:teacher_student_detail", args=[student.id])

        # Act
        response = client.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Assert
        no_notes_msg = soup.find(string=lambda text: text and "担任メモはまだありません" in text)
        assert no_notes_msg is not None, (
            "担任メモがない場合のメッセージが表示されていません。"
        )

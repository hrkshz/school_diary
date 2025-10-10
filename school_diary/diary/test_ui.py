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

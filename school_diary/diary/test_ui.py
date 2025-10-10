"""UI Element Tests for DiaryCreateView.

このファイルは連絡帳作成ページのUI要素が正しく表示されるかをテストします。
ブラウザテストではなく、Django TestClientとBeautifulSoupを使った自動テストです。

実行方法:
    dj pytest school_diary/diary/test_ui.py -v

テスト範囲:
    - フォーム要素の存在確認
    - ボタンの表示確認
    - CSRF保護の確認
    - ページタイトルとヘッダー確認
"""

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

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

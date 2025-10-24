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

"""
03-features.md System Features Tests

このモジュールは以下の機能をテストします:
- SYS-001: ヘルスチェック
- SYS-003: About

Traceability Matrix:
| Test Method | Feature ID | Scenario | Priority |
|-------------|------------|----------|----------|
| test_sys001_health_check_success | SYS-001 | 死活監視 | P2 |
| test_sys001_health_check_returns_json | SYS-001 | JSON形式 | P2 |
| test_sys003_about_display_success | SYS-003 | About表示 | P2 |
| test_sys003_about_unauthenticated_access | SYS-003 | 未認証アクセス | P2 |
"""

import json

import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestSYS001HealthCheck:
    """SYS-001: ヘルスチェックのテスト"""

    def test_sys001_health_check_success(self, client):
        """
        Given: システム稼働中
        When: /health/ にアクセス
        Then: 200 OK
        """
        # Act
        response = client.get(reverse("health"))

        # Assert
        assert response.status_code == 200

    def test_sys001_health_check_returns_json(self, client):
        """
        Given: システム稼働中
        When: /health/ にアクセス
        Then: JSON形式で {"status": "ok"} を返す
        """
        # Act
        response = client.get(reverse("health"))

        # Assert
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json"
        data = json.loads(response.content)
        assert data == {"status": "ok"}


@pytest.mark.django_db
class TestSYS003About:
    """SYS-003: Aboutページのテスト"""

    def test_sys003_about_display_success(self, authenticated_student_client):
        """
        Given: 認証済みユーザー
        When: /about/ にアクセス
        Then: システム概要が表示される
        """
        # Act
        response = authenticated_student_client.get(reverse("about"))

        # Assert
        assert response.status_code == 200
        assert "pages/about.html" in [t.name for t in response.templates]

    def test_sys003_about_unauthenticated_access(self, client):
        """
        Given: 未認証ユーザー
        When: /about/ にアクセス
        Then: 200 OK（公開ページ）
        """
        # Act
        response = client.get(reverse("about"))

        # Assert
        assert response.status_code == 200
        assert "pages/about.html" in [t.name for t in response.templates]

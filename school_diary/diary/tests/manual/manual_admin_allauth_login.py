"""
DJANGO_ADMIN_FORCE_ALLAUTH = True の動作確認テスト

シナリオ:
1. 未認証で /admin/ → /accounts/login/ にリダイレクト
2. ログイン成功 → /admin/ に到達
3. ログアウト → logged_out.html 表示
4. 「もう一度ログイン」(/admin/) → /accounts/login/ にリダイレクト
"""

import os

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

@pytest.mark.django_db
def test_admin_login_flow():
    """管理画面ログインフローテスト"""
    client = Client()

    print("=" * 60)
    print("DJANGO_ADMIN_FORCE_ALLAUTH 動作確認テスト")
    print("=" * 60)

    # Test 1: 未認証で /admin/ にアクセス
    print("\n[Test 1] 未認証で /admin/ にアクセス")
    response = client.get("/admin/", follow=False)
    print(f"  Status: {response.status_code}")
    print(f"  Redirect to: {response.get('Location', 'なし')}")

    if response.status_code == 302:
        redirect_url = response["Location"]
        if "/accounts/login/" in redirect_url:
            print("  ✅ /accounts/login/ にリダイレクト（allauth統一成功）")
        elif "/admin/login/" in redirect_url:
            print("  ❌ /admin/login/ にリダイレクト（Django標準、FORCE_ALLAUTH未適用）")
        else:
            print(f"  ⚠️  予期しないリダイレクト: {redirect_url}")

    # Test 2: allauthログインでadminにアクセス
    print("\n[Test 2] allauth経由でログイン")
    login_success = client.login(username="admin@example.com", password="password123")
    print(f"  Login success: {login_success}")

    if login_success:
        response = client.get("/admin/")
        print(f"  /admin/ Status: {response.status_code}")
        if response.status_code == 200:
            print("  ✅ 管理画面アクセス成功")
        else:
            print(f"  ❌ 管理画面アクセス失敗: {response.status_code}")

    # Test 3: ログアウト
    print("\n[Test 3] ログアウト")
    response = client.get("/admin/logout/", follow=True)
    print(f"  Status: {response.status_code}")
    print(f"  Final URL: {response.request['PATH_INFO']}")

    # ログアウト後のテンプレート確認
    content_str = response.content.decode("utf-8")
    if "Thanks for spending some quality time" in content_str or "ようこそ" in content_str:
        print("  ✅ jazzmin logged_out.html 表示")

    # Test 4: ログアウト後に /admin/ にアクセス（「もう一度ログイン」シナリオ）
    print("\n[Test 4] ログアウト後に /admin/ にアクセス（再ログインシナリオ）")
    response = client.get("/admin/", follow=False)
    print(f"  Status: {response.status_code}")

    if response.status_code == 302:
        redirect_url = response["Location"]
        print(f"  Redirect to: {redirect_url}")
        if "/accounts/login/" in redirect_url:
            print("  ✅ /accounts/login/ にリダイレクト（問題解決！）")
        elif "/admin/login/" in redirect_url:
            print("  ❌ /admin/login/ にリダイレクト（問題未解決）")

    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    test_admin_login_flow()

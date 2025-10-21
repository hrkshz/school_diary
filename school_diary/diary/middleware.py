"""パスワード変更強制ミドルウェア

管理者が仮パスワードで作成したユーザーの初回ログイン時に、
パスワード変更を強制するミドルウェア。
"""

from django.http import HttpResponseRedirect
from django.urls import reverse


class PasswordChangeRequiredMiddleware:
    """パスワード変更が必要なユーザーを強制的にパスワード変更画面にリダイレクト"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ログイン済みユーザーのみチェック
        if request.user.is_authenticated:
            # UserProfileが存在するかチェック
            if hasattr(request.user, "profile"):
                profile = request.user.profile

                # パスワード変更が必要な場合
                if profile.requires_password_change:
                    # 除外パス（無限ループ防止）
                    excluded_paths = [
                        "/admin/",  # 管理画面
                        "/accounts/logout/",  # ログアウト
                        "/accounts/password/change/",  # パスワード変更画面
                        "/static/",  # 静的ファイル
                        "/media/",  # メディアファイル
                    ]

                    # 現在のパスが除外パスに含まれていない場合
                    if not any(request.path.startswith(path) for path in excluded_paths):
                        # パスワード変更画面にリダイレクト
                        return HttpResponseRedirect(reverse("password_change"))

        return self.get_response(request)

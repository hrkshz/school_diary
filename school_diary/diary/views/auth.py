"""Auth and system views - home redirect, password change, health check."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render

from ..adapters import RoleBasedRedirectAdapter
from ..forms import PasswordChangeForm

__all__ = [
    "health_check",
    "home_redirect_view",
    "password_change_view",
]


def home_redirect_view(request):
    """ホームページのリダイレクト処理

    認証状態に応じて適切なページにリダイレクト:
    - 未認証ユーザー → ログインページ
    - ログイン済みユーザー → 役割別ダッシュボード（管理者/担任/生徒）
    """
    # 未認証ユーザー → ログインページ
    if not request.user.is_authenticated:
        return redirect("/accounts/login/")

    # ログイン済みユーザー → RoleBasedRedirectAdapterのロジックを再利用
    adapter = RoleBasedRedirectAdapter()
    redirect_url = adapter.get_login_redirect_url(request)
    return redirect(redirect_url)


@login_required
def password_change_view(request):
    """パスワード変更ビュー（初回ログイン時用）

    仮パスワードから本パスワードへの変更を行う。
    変更成功後、requires_password_changeをFalseに設定し、
    メールアドレスを認証済みにする。
    """
    from django.contrib.auth import update_session_auth_hash

    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # セッションを維持（パスワード変更後もログイン状態を保持）
            update_session_auth_hash(request, user)
            messages.success(request, "✅ パスワード変更が完了しました。メール認証も完了しました。")
            # 役割別ダッシュボードへリダイレクト
            return redirect("home")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, "diary/password_change.html", {"form": form})


def health_check(request):
    """ALB Health Check endpoint

    Returns HTTP 200 with JSON status for AWS Application Load Balancer health checks.
    This endpoint does not require authentication.
    """
    return JsonResponse({"status": "healthy"})

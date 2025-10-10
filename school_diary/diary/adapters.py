"""Custom allauth adapters for role-based redirect."""

from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class RoleBasedRedirectAdapter(DefaultAccountAdapter):
    """ロール別リダイレクト

    ログイン後、ユーザーの役割に応じて適切なページにリダイレクトします。

    - 管理者（is_staff=True）: Django Admin画面
    - 担任（ClassRoom.homeroom_teacherとして登録）: 担任ダッシュボード
    - 生徒: 生徒ダッシュボード
    """

    def get_login_redirect_url(self, request):
        """ログイン後のリダイレクト先を決定"""
        user = request.user

        # 管理者
        if user.is_staff:
            return "/admin/"

        # 担任（homeroom_teacherとして登録されている）
        if user.homeroom_classes.exists():
            return reverse("diary:teacher_dashboard")

        # 生徒
        return reverse("diary:student_dashboard")

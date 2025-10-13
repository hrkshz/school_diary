"""Custom allauth adapters for role-based redirect."""

from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class RoleBasedRedirectAdapter(DefaultAccountAdapter):
    """ロール別リダイレクトとメール正規化

    ログイン後、ユーザーの役割に応じて適切なページにリダイレクトします。

    - 管理者（is_staff=True）: Django Admin画面
    - 校長/教頭（role='school_leader'）: 学校全体ダッシュボード
    - 学年主任（role='grade_leader'）: 学年ダッシュボード
    - 担任（ClassRoom.homeroom_teacherとして登録）: 担任ダッシュボード
    - 生徒: 生徒ダッシュボード
    """

    def clean_email(self, email: str) -> str:
        """メールアドレスをバリデーション

        メールアドレスは小文字のみを許可します。
        大文字が含まれている場合はエラーを返します。

        Args:
            email: 入力されたメールアドレス

        Returns:
            バリデーション済みメールアドレス

        Raises:
            ValidationError: 大文字が含まれている場合
        """
        from django.core.exceptions import ValidationError

        email = email.strip()

        # 大文字が含まれている場合はエラー
        if email != email.lower():
            raise ValidationError(
                "メールアドレスは小文字のみ使用できます。"
            )

        return email

    def get_login_redirect_url(self, request):
        """ログイン後のリダイレクト先を決定"""
        user = request.user

        # 管理者
        if user.is_staff:
            return "/admin/"

        # 校長/教頭
        if user.profile.role == 'school_leader':
            return reverse("diary:school_overview")

        # 学年主任（担任と兼任の場合もこちら優先）
        if user.profile.role == 'grade_leader':
            return reverse("diary:grade_overview")

        # 担任（homeroom_teacherとして登録されている）
        if user.homeroom_classes.exists():
            return reverse("diary:teacher_dashboard")

        # 生徒
        return reverse("diary:student_dashboard")

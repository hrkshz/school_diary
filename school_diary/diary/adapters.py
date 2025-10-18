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

    def is_open_for_signup(self, request):  # noqa: ARG002
        """ユーザー登録を無効化

        管理画面からのみユーザー作成を許可するため、
        公開サインアップは無効化します。

        Args:
            request: HTTPリクエスト（このメソッドでは未使用）

        Returns:
            False: サインアップを無効化
        """
        return False

    def get_login_redirect_url(self, request):
        """ログイン後のリダイレクト先を決定

        ロールベースのリダイレクトを安全に実装。
        UserProfile が存在しない場合でも正常に動作します。

        優先順位:
        1. 管理者（is_staff=True） → Django Admin
        2. 校長/教頭（role='school_leader'） → 学校全体ダッシュボード
        3. 学年主任（role='grade_leader'） → 学年ダッシュボード
        4. 担任（ClassRoom.homeroom_teacher） → 担任ダッシュボード
        5. 生徒（デフォルト） → 生徒ダッシュボード

        Note:
            getattr()を使用してUserProfileに安全にアクセスしています。
            これにより、プロファイルが存在しない場合でも
            RelatedObjectDoesNotExist例外を回避できます。
        """
        user = request.user

        # 管理者（スーパーユーザーのみ、profileアクセス不要）
        if user.is_staff and user.is_superuser:
            return "/admin/"

        # プロファイルを安全に取得（存在しない場合はNone）
        profile = getattr(user, 'profile', None)

        if profile:
            # 校長/教頭
            if profile.role == 'school_leader':
                return reverse("diary:school_overview")

            # 学年主任（担任と兼任の場合もこちら優先）
            if profile.role == 'grade_leader':
                return reverse("diary:grade_overview")

            # 担任（roleが'teacher'またはhomeroom_teacherとして登録）
            if profile.role == 'teacher' or user.homeroom_classes.exists():
                return reverse("diary:teacher_dashboard")
        else:
            # プロファイルが存在しない場合でも担任チェック
            # （既存ユーザー互換性のため）
            if user.homeroom_classes.exists():
                return reverse("diary:teacher_dashboard")

        # 生徒（デフォルト）
        return reverse("diary:student_dashboard")

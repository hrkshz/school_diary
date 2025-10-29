from allauth.account.models import EmailAddress
from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Column
from crispy_forms.layout import Div
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
from crispy_forms.layout import Submit
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from .constants import GRADE_CHOICES_WITH_EMPTY
from .models import DiaryEntry
from .models import UserProfile
from .utils import get_previous_school_day

User = get_user_model()


# DiaryEntryFormの見出し定数
DIARY_FORM_LABELS = {
    "entry_date": "📅 記載日",
    "conditions": "😊 体調とメンタル",
    "reflection": "✍️ 今日の振り返り",
}


class DiaryEntryForm(forms.ModelForm):
    """連絡帳エントリーフォーム

    crispy-formsを活用してBootstrap 5スタイルの
    美しいフォームを自動生成する。
    """

    class Meta:
        model = DiaryEntry
        fields = ["entry_date", "health_condition", "mental_condition", "reflection"]
        widgets = {
            "entry_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"},
            ),
            "reflection": forms.Textarea(
                attrs={
                    "rows": 5,
                    "class": "form-control",
                    "placeholder": "今日はどんな1日でしたか？\n\n例：\n- 授業で学んだこと\n- 部活での出来事\n- 友達との交流",
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "diary-entry-form"

        self.helper.layout = Layout(
            Div(
                HTML(f'<h4 class="mb-3">{DIARY_FORM_LABELS["entry_date"]}</h4>'),
                "entry_date",
                HTML('<p class="form-text">前日の日付を選択してください</p>'),
                css_class="mb-4",
            ),
            Div(
                HTML(f'<h4 class="mb-3">{DIARY_FORM_LABELS["conditions"]}</h4>'),
                Row(
                    Column("health_condition", css_class="col-md-6"),
                    Column("mental_condition", css_class="col-md-6"),
                ),
                css_class="mb-4",
            ),
            Div(
                HTML(f'<h4 class="mb-3">{DIARY_FORM_LABELS["reflection"]}</h4>'),
                "reflection",
                css_class="mb-4",
            ),
            Submit("submit", "📝 提出する", css_class="btn btn-primary btn-lg w-100"),
        )

    def clean_entry_date(self):
        """記載日が前登校日であることを検証

        Returns:
            date: 検証済みの記載日

        Raises:
            ValidationError: 記載日が前登校日でない場合
        """
        entry_date = self.cleaned_data["entry_date"]
        today = timezone.now().date()
        expected_date = get_previous_school_day(today)

        if entry_date != expected_date:
            msg = f"記載日は前登校日（{expected_date.strftime('%Y年%m月%d日')}）にしてください。"
            raise ValidationError(
                msg,
            )

        return entry_date


class UserProfileAdminForm(forms.ModelForm):
    """ユーザープロフィール管理画面用フォーム

    管理学年を1, 2, 3のみに制限するChoiceFieldを使用。
    Django 5 + Jazzminのベストプラクティスに準拠。
    """

    managed_grade = forms.TypedChoiceField(
        choices=GRADE_CHOICES_WITH_EMPTY,
        coerce=lambda x: int(x) if x and x != "" else None,
        required=False,
        empty_value=None,
        widget=forms.Select,
        label="管理学年（学年主任のみ）",
        help_text="学年主任を選択した場合のみ入力してください",
    )

    class Meta:
        model = UserProfile
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data:
            return cleaned_data

        role = cleaned_data.get("role")
        managed_grade = cleaned_data.get("managed_grade")

        # 学年主任以外の場合、managed_gradeを自動的にNoneにクリア
        if role != UserProfile.ROLE_GRADE_LEADER:
            cleaned_data["managed_grade"] = None

        # 学年主任の場合、managed_gradeが必須
        elif role == UserProfile.ROLE_GRADE_LEADER and not managed_grade:
            self.add_error(
                "managed_grade",
                "学年主任の場合、管理学年の入力が必須です",
            )

        return cleaned_data


class CustomUserCreationForm(UserCreationForm):
    """カスタムユーザー作成フォーム（管理画面用）

    1画面で以下を設定可能:
    - メールアドレス（ログイン用）
    - 姓名（日本式）
    - 役割（UserProfile）
    - 管理学年（学年主任のみ）
    - パスワード

    ユーザー名は姓+名で自動生成されます。
    """

    email = forms.EmailField(
        required=True,
        label="メールアドレス",
        help_text="ログイン時に使用されます",
    )
    last_name = forms.CharField(
        required=True,
        max_length=150,
        label="姓",
        help_text="例: 山田",
    )
    first_name = forms.CharField(
        required=True,
        max_length=150,
        label="名",
        help_text="例: 太郎",
    )
    role = forms.ChoiceField(
        choices=UserProfile.ROLE_CHOICES,
        required=True,
        label="役割",
    )
    managed_grade = forms.TypedChoiceField(
        choices=GRADE_CHOICES_WITH_EMPTY,
        coerce=lambda x: int(x) if x and x != "" else None,
        required=False,
        empty_value=None,
        label="管理学年",
        help_text="学年主任の場合のみ選択してください",
    )

    class Meta:
        model = User
        fields = ("email", "last_name", "first_name", "role", "managed_grade", "password1", "password2")

    def clean_email(self):
        """メールアドレスの重複チェック"""
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            msg = "このメールアドレスは既に使用されています。"
            raise ValidationError(msg)
        return email

    def clean(self):
        """学年主任の場合、管理学年が必須"""
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        managed_grade = cleaned_data.get("managed_grade")

        if role == UserProfile.ROLE_GRADE_LEADER and not managed_grade:
            self.add_error("managed_grade", "学年主任の場合、管理学年の選択が必須です。")

        return cleaned_data

    def save(self, commit=True):
        """ユーザーとUserProfileを作成

        - username: 姓+名で自動生成（重複時は連番追加）
        - is_staff: 生徒以外はTrue
        - UserProfile.role: フォームで選択した役割
        - EmailAddress: verified=True（管理者作成なので認証済み）
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.last_name = self.cleaned_data["last_name"]
        user.first_name = self.cleaned_data["first_name"]

        # ユーザー名を姓+名で生成（重複時は連番追加）
        base_username = f"{user.last_name}{user.first_name}"
        username = base_username
        counter = 2
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username

        # 生徒以外はis_staffをTrue
        role = self.cleaned_data["role"]
        if role != UserProfile.ROLE_STUDENT:
            user.is_staff = True

        if commit:
            user.save()

            # UserProfileを更新（signals.pyで自動作成済み）
            profile = user.profile
            profile.role = role
            managed_grade = self.cleaned_data.get("managed_grade")
            if managed_grade:
                profile.managed_grade = managed_grade
            profile.save()

            # メールアドレスを認証済みとして登録
            # Note: signals.pyで自動作成されるが、念のためget_or_create()で冪等性を保つ
            EmailAddress.objects.get_or_create(
                user=user,
                email=user.email.lower(),
                defaults={
                    "verified": True,
                    "primary": True,
                },
            )

        return user


class PasswordChangeForm(forms.Form):
    """パスワード変更フォーム（初回ログイン時用）

    仮パスワードから本パスワードへの変更を行うフォーム。
    """

    old_password = forms.CharField(
        label="現在のパスワード（仮パスワード）",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "メールで送信された仮パスワード"}),
        help_text="管理者から送信されたメールに記載されている仮パスワードを入力してください。",
    )
    new_password1 = forms.CharField(
        label="新しいパスワード",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "8文字以上の安全なパスワード"}),
        help_text="8文字以上で、他人に推測されにくいパスワードを設定してください。",
    )
    new_password2 = forms.CharField(
        label="新しいパスワード（確認）",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "もう一度入力してください"}),
        help_text="確認のため、もう一度同じパスワードを入力してください。",
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(
                HTML('<h4 class="mb-3">🔒 パスワード変更</h4>'),
                HTML('<p class="text-muted">初回ログインのため、パスワードを変更してください。</p>'),
                css_class="mb-4",
            ),
            "old_password",
            "new_password1",
            "new_password2",
            Submit("submit", "パスワードを変更する", css_class="btn btn-primary btn-lg w-100 mt-3"),
        )

    def clean_old_password(self):
        """現在のパスワード（仮パスワード）が正しいか検証"""
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            error_message = "現在のパスワードが正しくありません。"
            raise ValidationError(error_message)
        return old_password

    def clean_new_password2(self):
        """新しいパスワードが一致するか検証"""
        new_password1 = self.cleaned_data.get("new_password1")
        new_password2 = self.cleaned_data.get("new_password2")
        if new_password1 and new_password2 and new_password1 != new_password2:
            error_message = "新しいパスワードが一致しません。"
            raise ValidationError(error_message)
        return new_password2

    def save(self, commit=True):
        """パスワードを変更して、requires_password_changeをFalseに設定"""
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if hasattr(self.user, "profile"):
            self.user.profile.requires_password_change = False
            self.user.profile.save()

        # メールアドレスを認証済みにする
        email_address = EmailAddress.objects.filter(user=self.user, email=self.user.email).first()
        if email_address:
            email_address.verified = True
            email_address.save()

        if commit:
            self.user.save()
        return self.user


class TestDataConfigForm(forms.Form):
    """テストデータ作成設定フォーム"""

    clean_existing = forms.BooleanField(
        label="既存データをクリア",
        required=False,
        help_text="⚠️ 全ての既存テストデータが削除されます。この操作は取り消せません。",
    )

    diary_days = forms.IntegerField(
        label="日記作成日数",
        initial=30,
        min_value=1,
        max_value=30,
        help_text="過去何日分の日記を作成するか（1〜30日）",
    )

    students_per_class = forms.IntegerField(
        label="生徒数/クラス",
        initial=30,
        min_value=1,
        max_value=30,
        help_text="各クラスに作成する生徒数（1〜30名）",
    )

    include_special_patterns = forms.BooleanField(
        label="特別パターンを含める",
        initial=True,
        required=False,
        help_text="P0/P1/P1.5等の特別なテストパターンを作成",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.layout = Layout(
            Div(
                HTML('<div class="alert alert-warning"><h5>⚠️ 注意事項</h5><p>テストデータを作成します。設定を確認してください。</p></div>'),
                css_class="mb-4",
            ),
            Div(
                "clean_existing",
                css_class="mb-3",
            ),
            Row(
                Column("diary_days", css_class="col-md-6"),
                Column("students_per_class", css_class="col-md-6"),
                css_class="mb-3",
            ),
            Div(
                "include_special_patterns",
                css_class="mb-4",
            ),
            Div(
                HTML('<a href="{% url \'admin:index\' %}" class="btn btn-secondary me-2"><i class="bi bi-arrow-left me-2"></i>キャンセル</a>'),
                Submit("submit", "次へ", css_class="btn btn-primary"),
                css_class="d-flex justify-content-between",
            ),
        )

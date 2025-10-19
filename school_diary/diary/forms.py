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
                HTML('<h4 class="mb-3">📅 記載日</h4>'),
                "entry_date",
                HTML('<p class="form-text">前日の日付を選択してください</p>'),
                css_class="mb-4",
            ),
            Div(
                HTML('<h4 class="mb-3">😊 体調とメンタル</h4>'),
                Row(
                    Column("health_condition", css_class="col-md-6"),
                    Column("mental_condition", css_class="col-md-6"),
                ),
                css_class="mb-4",
            ),
            Div(
                HTML('<h4 class="mb-3">✍️ 今日の振り返り</h4>'),
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
            raise ValidationError(
                f"記載日は前登校日（{expected_date.strftime('%Y年%m月%d日')}）にしてください。",
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
        if role != "grade_leader":
            cleaned_data["managed_grade"] = None

        # 学年主任の場合、managed_gradeが必須
        elif role == "grade_leader" and not managed_grade:
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
            raise ValidationError("このメールアドレスは既に使用されています。")
        return email

    def clean(self):
        """学年主任の場合、管理学年が必須"""
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        managed_grade = cleaned_data.get("managed_grade")

        if role == "grade_leader" and not managed_grade:
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
        if role != "student":
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
            EmailAddress.objects.create(
                user=user,
                email=user.email,
                verified=True,
                primary=True,
            )

        return user

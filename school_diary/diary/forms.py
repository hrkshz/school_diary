from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Column
from crispy_forms.layout import Div
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
from crispy_forms.layout import Submit
from django import forms

from .models import DiaryEntry
from .models import UserProfile


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


class UserProfileAdminForm(forms.ModelForm):
    """ユーザープロフィール管理画面用フォーム

    管理学年を1, 2, 3のみに制限するChoiceFieldを使用。
    Django 5 + Jazzminのベストプラクティスに準拠。
    """

    managed_grade = forms.TypedChoiceField(
        choices=[("", "---"), (1, "1年"), (2, "2年"), (3, "3年")],
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
        role = cleaned_data.get('role')
        managed_grade = cleaned_data.get('managed_grade')

        # 学年主任以外の場合、managed_gradeを自動的にNoneにクリア
        if role != 'grade_leader':
            cleaned_data['managed_grade'] = None

        # 学年主任の場合、managed_gradeが必須
        elif role == 'grade_leader' and not managed_grade:
            self.add_error(
                'managed_grade',
                '学年主任の場合、管理学年の入力が必須です'
            )

        return cleaned_data

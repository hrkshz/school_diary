from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML
from crispy_forms.layout import Column
from crispy_forms.layout import Div
from crispy_forms.layout import Layout
from crispy_forms.layout import Row
from crispy_forms.layout import Submit
from django import forms

from .models import DiaryEntry


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
                attrs={"type": "date", "class": "form-control"}
            ),
            "reflection": forms.Textarea(
                attrs={
                    "rows": 5,
                    "class": "form-control",
                    "placeholder": "今日はどんな1日でしたか？\n\n例：\n- 授業で学んだこと\n- 部活での出来事\n- 友達との交流",
                }
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

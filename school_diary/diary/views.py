"""Views for diary app."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.views.generic import TemplateView

from .models import DiaryEntry


class StudentDashboardView(LoginRequiredMixin, TemplateView):
    """生徒用ダッシュボード

    生徒がログイン後に表示されるメインページ。
    過去7日分の連絡帳と提出状況を表示。
    """

    template_name = "diary/student_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 過去7日分の連絡帳
        context["recent_entries"] = (
            DiaryEntry.objects.filter(student=self.request.user)
            .select_related("read_by")
            .order_by("-entry_date")[:7]
        )

        # 今日の提出済みか確認
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        context["today_submitted"] = DiaryEntry.objects.filter(
            student=self.request.user,
            entry_date=yesterday,
        ).exists()

        return context


class TeacherDashboardView(TemplateView):
    """担任用ダッシュボード

    担任がログイン後に表示されるメインページ。
    """

    template_name = "diary/teacher_dashboard.html"


# 以下はダミー実装（MLP-6, MLP-7で本実装予定）
class DiaryCreateView(LoginRequiredMixin, TemplateView):
    """連絡帳作成ページ（ダミー）"""

    template_name = "diary/diary_create.html"


class DiaryHistoryView(LoginRequiredMixin, TemplateView):
    """過去記録閲覧ページ（ダミー）"""

    template_name = "diary/diary_history.html"

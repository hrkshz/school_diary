"""Views for diary app."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView
from django.views.generic import ListView
from django.views.generic import TemplateView

from .forms import DiaryEntryForm
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


class DiaryCreateView(LoginRequiredMixin, CreateView):
    """連絡帳作成ページ

    生徒が連絡帳を新規作成するページ。
    一日一件の制約をチェックし、重複を防ぐ。
    """

    model = DiaryEntry
    form_class = DiaryEntryForm
    template_name = "diary/diary_create.html"
    success_url = reverse_lazy("diary:student_dashboard")

    def form_valid(self, form):
        """フォーム送信時の処理

        生徒を設定し、一日一件制約をチェック。
        重複がある場合はエラーメッセージを表示してリダイレクト。
        """
        # 生徒を設定
        form.instance.student = self.request.user

        # 一日一件制約チェック
        entry_date = form.cleaned_data["entry_date"]
        if DiaryEntry.objects.filter(
            student=self.request.user,
            entry_date=entry_date,
        ).exists():
            messages.error(
                self.request,
                f"{entry_date}の連絡帳は既に作成済みです。",
            )
            return redirect("diary:student_dashboard")

        # 保存成功メッセージ
        messages.success(self.request, "連絡帳を作成しました。")
        return super().form_valid(form)


class DiaryHistoryView(LoginRequiredMixin, ListView):
    """過去記録閲覧ページ

    生徒の過去の連絡帳を一覧表示。
    ページネーションと月別フィルタリングに対応。
    """

    model = DiaryEntry
    template_name = "diary/diary_history.html"
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self):
        """ログイン中の生徒の連絡帳のみ取得"""
        return (
            DiaryEntry.objects.filter(student=self.request.user)
            .select_related("read_by")
            .order_by("-entry_date")
        )

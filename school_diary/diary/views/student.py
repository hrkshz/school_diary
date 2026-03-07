"""Student views - dashboard, diary CRUD, history."""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView

from ..forms import DiaryEntryForm
from ..models import DiaryEntry
from ..services.diary_entry_service import DiaryEntryService
from ..utils import get_previous_school_day

__all__ = [
    "StudentDashboardView",
    "DiaryCreateView",
    "DiaryUpdateView",
    "DiaryHistoryView",
]


class StudentDashboardView(LoginRequiredMixin, TemplateView):
    """生徒用ダッシュボード

    生徒がログイン後に表示されるメインページ。
    過去7日分の連絡帳と提出状況を表示。
    """

    template_name = "diary/student_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 過去7日分の連絡帳
        context["entries"] = (
            DiaryEntry.objects.filter(student=self.request.user).select_related("read_by").order_by("-entry_date")[:7]
        )

        # 今日の提出済みか確認（前登校日ベース）
        expected_date = get_previous_school_day(timezone.now().date())
        context["today_submitted"] = DiaryEntry.objects.filter(
            student=self.request.user,
            entry_date=expected_date,
        ).exists()

        # リマインダー表示判定
        context["has_reminder"] = not context["today_submitted"]
        context["reminder_date"] = expected_date

        return context


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

        Note:
            DiaryEntryServiceを使用してビジネスロジックを分離
        """
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

        # DiaryEntryServiceを使用して作成（ビジネスロジック分離）
        DiaryEntryService.create_entry(
            student=self.request.user,
            entry_date=entry_date,
            health_condition=form.cleaned_data["health_condition"],
            mental_condition=form.cleaned_data["mental_condition"],
            reflection=form.cleaned_data["reflection"],
        )

        # 保存成功メッセージ
        messages.success(self.request, "連絡帳を作成しました。")
        return redirect(self.success_url)


class DiaryUpdateView(LoginRequiredMixin, UpdateView):
    """連絡帳編集ページ（S-02: 既読前のみ編集可）

    生徒が既読前の連絡帳を編集するページ。
    既読後は過去記録化されるため編集不可。

    セキュリティ:
    - LoginRequiredMixin: 未認証ユーザーをブロック
    - get_queryset(): 自分のエントリーで、かつ未既読のもののみ取得
    """

    model = DiaryEntry
    form_class = DiaryEntryForm
    template_name = "diary/diary_update.html"
    success_url = reverse_lazy("diary:student_dashboard")

    def get_object(self, queryset=None):
        """セキュリティ: 自分の未既読エントリーのみ編集可能

        権限チェック順序:
        1. エントリーを取得（IDの存在確認）
        2. 所有者チェック（他生徒は403）
        3. 編集可能チェック（既読後は403）
        """
        obj = super().get_object(queryset)

        # 他生徒のエントリーは403
        if obj.student != self.request.user:
            msg = "他の生徒の連絡帳は編集できません。"
            raise PermissionDenied(msg)

        # 既読後は403
        if obj.is_read:
            msg = "既読後の連絡帳は編集できません。"
            raise PermissionDenied(msg)

        return obj

    def form_valid(self, form):
        """フォーム送信時の処理

        編集成功メッセージを表示。

        Note:
            DiaryEntryServiceを使用してビジネスロジックを分離
        """
        # DiaryEntryServiceを使用して更新（ビジネスロジック分離）
        entry = self.get_object()
        DiaryEntryService.update_entry(
            entry=entry,
            health_condition=form.cleaned_data["health_condition"],
            mental_condition=form.cleaned_data["mental_condition"],
            reflection=form.cleaned_data["reflection"],
        )

        messages.success(self.request, "連絡帳を更新しました。")
        return redirect(self.success_url)


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
        return DiaryEntry.objects.filter(student=self.request.user).select_related("read_by").order_by("-entry_date")

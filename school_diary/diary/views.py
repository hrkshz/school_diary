"""Views for diary app."""

import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotAllowed
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView

from . import alert_service
from .adapters import RoleBasedRedirectAdapter
from .constants import DashboardSettings
from .constants import GradeLevel
from .constants import HealthThresholds
from .constants import NoteSettings
from .forms import DiaryEntryForm
from .forms import PasswordChangeForm
from .models import AbsenceReason
from .models import ActionStatus
from .models import AttendanceStatus
from .models import ClassRoom
from .models import DailyAttendance
from .models import DiaryEntry
from .models import PublicReaction
from .models import TeacherNote
from .models import TeacherNoteReadStatus
from .services.diary_entry_service import DiaryEntryService
from .services.teacher_dashboard_service import TeacherDashboardService
from .utils import check_consecutive_decline
from .utils import check_critical_mental_state
from .utils import get_previous_school_day

# グローバル変数として User を定義（関数内importを避けるため）
User = get_user_model()


def get_students_with_consecutive_decline(
    classroom,
    days=HealthThresholds.CONSECUTIVE_DAYS,
    threshold=HealthThresholds.POOR_CONDITION,
):
    """3日連続で体調/メンタルが低下している生徒を検出

    いじめ・不登校の早期発見のため、継続的な不調を検知する。

    Args:
        classroom: 対象クラス (ClassRoomインスタンス)
        days: 連続日数 (デフォルト3日、設計判断: 2日では誤検知多い、4日では遅い)
        threshold: 閾値 (≤この値で「低下」と判定、デフォルト2)
                  1=とても悪い、2=悪い、3=普通、4=良い、5=とても良い

    Returns:
        tuple: (体調低下生徒リスト, メンタル低下生徒リスト)

    パフォーマンス:
        - O(n) where n = 生徒数
        - N+1問題回避 (select_related使用)
        - 35名クラスで数ミリ秒

    設計判断:
        - 厳密に連続 (最新3日間が連続で≤2)
        - 未提出日は除外 (提出されたデータのみで判断)
        - 体調とメンタルを個別に検出 (両方低下の場合も別々にカウント)
    """
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days - 1)

    # 過去3日分の連絡帳を取得（N+1問題回避）
    entries = (
        DiaryEntry.objects.filter(
            student__classes=classroom,
            entry_date__gte=start_date,
            entry_date__lte=end_date,
        )
        .select_related("student")
        .order_by("student", "-entry_date")
    )

    # 生徒ごとにグループ化して連続性をチェック
    students_health_decline = []
    students_mental_decline = []

    for student in classroom.students.all():
        # この生徒の連絡帳を抽出
        student_entries = [e for e in entries if e.student_id == student.id]

        # 最新3件が揃っている場合のみチェック（未提出日は除外）
        if len(student_entries) >= days:
            recent_entries = student_entries[:days]

            # 全て閾値以下かチェック（all()で厳密な連続性を確認）
            if all(e.health_condition <= threshold for e in recent_entries):
                students_health_decline.append(student)

            if all(e.mental_condition <= threshold for e in recent_entries):
                students_mental_decline.append(student)

    return students_health_decline, students_mental_decline


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


class TeacherDashboardView(LoginRequiredMixin, TemplateView):
    """担任用ダッシュボード

    担任がログイン後に表示されるメインページ。
    担当クラスの生徒一覧、未読件数、最新の体調・メンタルを表示。
    """

    template_name = "diary/teacher_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 担当クラスを取得
        classroom = self.request.user.homeroom_classes.first()

        if not classroom:
            context["classroom"] = None
            context["students"] = []
            context["summary"] = {
                "unread_total": 0,
                "poor_health_count": 0,
                "poor_mental_count": 0,
                "not_submitted_today": 0,
                "urgent_action_count": 0,
                "pending_action_count": 0,
            }
            context["filter_type"] = "all"
            return context

        today = timezone.now().date()

        # サマリー統計を取得（Service層）
        summary_stats = TeacherDashboardService.get_classroom_summary(classroom)

        # 生徒一覧を取得（Service層）
        students = TeacherDashboardService.get_student_list_with_unread_count(classroom)

        # テンプレート用にデータ整形
        student_data = []
        for student in students:
            latest_entry = student.latest_entry_list[0] if student.latest_entry_list else None
            # テーブルビュー用: 本日の連絡帳のみに絞る（時点統一）
            today_entry = latest_entry if (latest_entry and latest_entry.entry_date == today) else None
            student_data.append(
                {
                    "student": student,
                    "unread_count": student.unread_count,
                    "latest_entry": today_entry,
                },
            )

        # Table View用: 本日の未提出者数を計算
        today_not_submitted_count = sum(1 for s in student_data if s["latest_entry"] is None)

        # 欠席者情報を取得（Service層）
        absence_data = TeacherDashboardService.get_absence_data(classroom, today)

        # 出席データを取得（Service層）
        student_data, all_students = TeacherDashboardService.get_attendance_data_for_modal(
            classroom,
            today,
            student_data,
        )

        context["classroom"] = classroom
        context["students"] = student_data
        context["today"] = today
        context["summary"] = summary_stats
        context["today_not_submitted_count"] = today_not_submitted_count
        context["absence_data"] = absence_data
        context["all_students"] = all_students

        # アラート生成（MAP-2A: 早期警告システム）
        alerts = []

        # 全生徒をチェック（フィルタに依存しない早期警告）
        for student in classroom.students.all():
            # Level 1: Critical - メンタル★1（即座の対応が必要）
            mental_state = check_critical_mental_state(student)
            if mental_state["has_alert"]:
                alerts.append(
                    {
                        "level": "critical",
                        "type": "mental_critical",
                        "student": student,
                        "message": f"{student.get_full_name()}さん - メンタル★1",
                        "date": mental_state["date"],
                        "action": "声をかけてください。",
                    },
                )

            # Level 3: Warning - メンタル3日連続低下
            mental_decline = check_consecutive_decline(student, "mental_condition")
            if mental_decline["has_alert"]:
                trend_values = mental_decline["trend"]
                trend_str = " → ".join([f"★{'★' * v}" for v in trend_values])
                alerts.append(
                    {
                        "level": "warning",
                        "type": "mental_decline",
                        "student": student,
                        "message": f"{student.get_full_name()}さん - メンタル低下が続いています",
                        "trend": trend_str,
                        "dates": mental_decline["dates"],
                        "action": "注意して見守ってください。",
                    },
                )

        # Level 4: Warning - クラス5人以上が体調不良
        previous_date = get_previous_school_day(today)
        poor_health_count = DiaryEntry.objects.filter(
            student__classes=classroom,
            entry_date=previous_date,
            health_condition__lte=HealthThresholds.POOR_CONDITION,
        ).count()

        if poor_health_count >= HealthThresholds.CLASS_ALERT_THRESHOLD:
            alerts.append(
                {
                    "level": "warning",
                    "type": "class_health",
                    "message": f"クラス全体 - 体調不良が多いです（{poor_health_count}名）",
                    "date": previous_date,
                    "action": "注意してください。",
                },
            )

        context["alerts"] = alerts

        # Inbox Pattern: 6カテゴリ分類（Important/NeedsAttention/NeedsAction/NotSubmitted/Unread/Completed）
        classified_students = alert_service.classify_students(classroom)

        # 未対応の合計を計算（テンプレート側での複雑な計算を避ける）
        needs_response_count = (
            len(classified_students["not_submitted"])
            + len(classified_students["unread"])
        )

        # 各分類の生徒に最新3件の連絡帳をprefetch（N+1問題回避、履歴表示用）
        for tier in ["important", "needs_attention", "not_submitted", "unread"]:
            student_ids = [s.id for s in classified_students[tier]]
            if student_ids:
                # prefetch_relatedで最新3件を取得（履歴統合用）
                students_with_history = list(
                    classroom.students.filter(id__in=student_ids).prefetch_related(
                        Prefetch(
                            "diary_entries",
                            queryset=DiaryEntry.objects.order_by("-entry_date")[:3],
                            to_attr="recent_entries_for_history",
                        ),
                    ),
                )

                # 各生徒に履歴文字列を追加
                for student in students_with_history:
                    if hasattr(student, "recent_entries_for_history") and student.recent_entries_for_history:
                        student.inline_history = alert_service.format_inline_history(
                            student.recent_entries_for_history,
                        )
                        student.latest_snippet = alert_service.get_snippet(
                            student.recent_entries_for_history[0],
                        )
                        # カードボタン用にlatest_entry_idを設定
                        student.latest_entry_id = student.recent_entries_for_history[0].id
                    else:
                        student.inline_history = ""
                        student.latest_snippet = "未提出"
                        student.latest_entry_id = None

                classified_students[tier] = students_with_history

        # completedは (student, date) のタプルのリストなので、studentのみ抽出してprefetch
        completed_tuples = classified_students["completed"]
        if completed_tuples:
            completed_student_ids = [s.id for s, _ in completed_tuples]
            students_with_history = list(
                classroom.students.filter(id__in=completed_student_ids).prefetch_related(
                    Prefetch(
                        "diary_entries",
                        queryset=DiaryEntry.objects.order_by("-entry_date")[:3],
                        to_attr="recent_entries_for_history",
                    ),
                ),
            )

            # 各生徒に履歴文字列を追加 + 日付情報を保持
            students_with_dates = []
            for student in students_with_history:
                # タプルから日付を取得
                entry_date = next(d for s, d in completed_tuples if s.id == student.id)

                if hasattr(student, "recent_entries_for_history") and student.recent_entries_for_history:
                    student.inline_history = alert_service.format_inline_history(
                        student.recent_entries_for_history,
                    )
                    student.latest_snippet = alert_service.get_snippet(
                        student.recent_entries_for_history[0],
                    )
                    # カードボタン用にlatest_entry_idを設定
                    student.latest_entry_id = student.recent_entries_for_history[0].id
                else:
                    student.inline_history = ""
                    student.latest_snippet = "未提出"
                    student.latest_entry_id = None

                # 日付情報を付加
                student.completed_date = entry_date
                students_with_dates.append(student)

            classified_students["completed"] = students_with_dates

        # needs_actionは (student, entry) のタプルのリストなので、studentのみ抽出してprefetch
        needs_action_tuples = classified_students["needs_action"]
        if needs_action_tuples:
            needs_action_student_ids = [s.id for s, _ in needs_action_tuples]
            students_with_history = list(
                classroom.students.filter(id__in=needs_action_student_ids).prefetch_related(
                    Prefetch(
                        "diary_entries",
                        queryset=DiaryEntry.objects.order_by("-entry_date")[:3],
                        to_attr="recent_entries_for_history",
                    ),
                ),
            )

            # 各生徒に履歴文字列 + entryの詳細情報を追加
            students_with_action_details = []
            for student in students_with_history:
                # タプルからentryを取得
                entry = next(e for s, e in needs_action_tuples if s.id == student.id)

                if hasattr(student, "recent_entries_for_history") and student.recent_entries_for_history:
                    student.inline_history = alert_service.format_inline_history(
                        student.recent_entries_for_history,
                    )
                    student.latest_snippet = alert_service.get_snippet(
                        student.recent_entries_for_history[0],
                    )
                else:
                    student.inline_history = ""
                    student.latest_snippet = "未提出"

                # internal_action情報を付加
                student.internal_action = entry.internal_action
                student.internal_action_label = entry.get_internal_action_display()
                student.action_status = entry.action_status
                student.entry_date = entry.entry_date
                student.action_entry_id = entry.id
                # カードボタン用にlatest_entry_idを設定（P1.5では action_entry_id と同じ）
                student.latest_entry_id = entry.id
                students_with_action_details.append(student)

            classified_students["needs_action"] = students_with_action_details

        context["classified_students"] = classified_students
        context["needs_response_count"] = needs_response_count

        # 学年共有メモを取得（Service層）
        shared_notes = TeacherDashboardService.get_shared_notes(classroom, self.request.user)
        context["shared_notes"] = shared_notes

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


class TeacherStudentDetailView(LoginRequiredMixin, ListView):
    """担任用個別生徒詳細ページ

    担任が個別生徒の連絡帳履歴を時系列で表示。
    未読エントリーを強調表示し、既読処理が可能。
    """

    model = DiaryEntry
    template_name = "diary/teacher_student_detail.html"
    context_object_name = "entries"
    paginate_by = 10

    def get_queryset(self):
        """担当クラスの生徒の連絡帳のみ取得

        権限チェック: 担任が自分のクラスの生徒のみアクセス可能。
        存在しない生徒や他のクラスの生徒の場合は404エラー。
        """
        student_id = self.kwargs.get("student_id")

        # 担任のクラスを取得
        classroom = self.request.user.homeroom_classes.first()
        if not classroom:
            return DiaryEntry.objects.none()  # 担任でない場合は空のクエリセット

        # クラスの生徒の連絡帳のみ取得（存在しない場合は404）
        return (
            DiaryEntry.objects.filter(
                student_id=student_id,
                student__classes=classroom,
            )
            .select_related("read_by", "student", "action_completed_by")
            .order_by("-entry_date")
        )

    def get_context_data(self, **kwargs):
        """テンプレートコンテキストに生徒情報、未読件数、担任メモを追加"""
        context = super().get_context_data(**kwargs)

        # 生徒情報を取得
        student_id = self.kwargs.get("student_id")
        classroom = self.request.user.homeroom_classes.first()

        if classroom:
            student = get_object_or_404(
                User,
                id=student_id,
                classes=classroom,
            )
            context["student"] = student

            # 未読件数を計算
            unread_count = DiaryEntry.objects.filter(
                student=student,
                is_read=False,
            ).count()
            context["unread_count"] = unread_count

            # 担任メモを取得（権限チェック: 自分のクラスの生徒のメモのみ）
            # 共有メモは学年の全担任が閲覧可能、非共有メモは作成者のみ
            notes = (
                TeacherNote.objects.filter(
                    student=student,
                )
                .filter(
                    Q(is_shared=True) | Q(teacher=self.request.user),
                )
                .select_related("teacher")
                .order_by("-updated_at")
            )
            context["notes"] = notes

        return context


@login_required
def teacher_mark_as_read(request, diary_id):
    """担任用既読処理・反応対応更新

    POSTリクエストで連絡帳を既読にする、または既読済み連絡帳の反応・対応記録を更新する。
    権限チェック: 担任が自分のクラスの生徒の連絡帳のみ操作可能。

    変更内容:
    - 既読処理と反応・対応の更新を分離
    - 既読済みの連絡帳でも反応・対応を追加/変更/削除可能
    - 空文字列の送信で反応・対応を削除可能
    - action_statusの自動管理（対応記録設定時にpending、削除時にNULL）
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    # 担任のクラスを取得
    classroom = request.user.homeroom_classes.first()
    if not classroom:
        return HttpResponseForbidden()

    # 連絡帳を取得
    diary = get_object_or_404(DiaryEntry, id=diary_id)

    # クラスの生徒のもののみアクセス可能
    if diary.student not in classroom.students.all():
        return HttpResponseForbidden("このクラスの生徒の連絡帳ではありません。")

    # 既読状態を記録
    was_already_read = diary.is_read

    # 既読処理（未読の場合のみ）
    if not diary.is_read:
        diary.is_read = True
        diary.read_by = request.user
        diary.read_at = timezone.now()

    # 反応・対応は常に更新可能（既読かどうかに関わらず）
    if "public_reaction" in request.POST:
        reaction_value = request.POST.get("public_reaction", "").strip()
        diary.public_reaction = reaction_value if reaction_value else None

    if "internal_action" in request.POST:
        action_value = request.POST.get("internal_action", "").strip()
        diary.internal_action = action_value if action_value else None

        # action_statusの管理
        if action_value:
            # 対応記録が設定された場合、常にPENDINGにする
            # （NOT_REQUIRED、COMPLETED、PENDINGのいずれからでも更新可能）
            diary.action_status = ActionStatus.PENDING
        else:
            # 対応記録が削除された場合、ステータスをNOT_REQUIREDに設定
            # （以前はsave()メソッドに依存していたが、明示的に設定するように変更）
            diary.action_status = ActionStatus.NOT_REQUIRED

    diary.save()

    # メッセージ
    if was_already_read:
        messages.success(
            request,
            f"{diary.student.get_full_name()}さんの{diary.entry_date}の反応・対応記録を更新しました。",
        )
    else:
        messages.success(
            request,
            f"{diary.student.get_full_name()}さんの{diary.entry_date}の連絡帳を既読にしました。",
        )

    # 個別生徒詳細ページにリダイレクト
    return redirect("diary:teacher_student_detail", student_id=diary.student.id)


@login_required
def teacher_mark_action_completed(request, diary_id):
    """担任用対応完了処理

    POSTリクエストで連絡帳のアクションを対応済みにする。
    権限チェック: 担任が自分のクラスの生徒の連絡帳のみ対応可能。
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    # 担任のクラスを取得
    classroom = request.user.homeroom_classes.first()
    if not classroom:
        return HttpResponseForbidden()

    # 連絡帳を取得（クラスの生徒のもののみ）
    diary = get_object_or_404(
        DiaryEntry,
        id=diary_id,
        student__classes=classroom,
    )

    # 対応内容メモを取得
    action_note = request.POST.get("action_note", "").strip()

    # 対応完了処理
    diary.mark_action_completed(request.user, note=action_note)

    messages.success(
        request,
        f"{diary.student.get_full_name()}さんの{diary.entry_date}の対応を完了にしました。",
    )

    # 生徒詳細ページにリダイレクト
    return redirect("diary:teacher_student_detail", student_id=diary.student.id)


def home_redirect_view(request):
    """ホームページのリダイレクト処理

    認証状態に応じて適切なページにリダイレクト:
    - 未認証ユーザー → ログインページ
    - ログイン済みユーザー → 役割別ダッシュボード（管理者/担任/生徒）
    """
    # 未認証ユーザー → ログインページ
    if not request.user.is_authenticated:
        return redirect("/accounts/login/")

    # ログイン済みユーザー → RoleBasedRedirectAdapterのロジックを再利用
    adapter = RoleBasedRedirectAdapter()
    redirect_url = adapter.get_login_redirect_url(request)
    return redirect(redirect_url)


@login_required
def teacher_add_note(request, student_id):
    """担任メモ追加

    POSTリクエストで担任メモを追加する。
    権限チェック: 担任が自分のクラスの生徒にのみメモを追加可能。
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    # 担任のクラスを取得
    classroom = request.user.homeroom_classes.first()
    if not classroom:
        return HttpResponseForbidden()

    # 生徒を取得（自分のクラスの生徒のみ）
    student = get_object_or_404(User, id=student_id, classes=classroom)

    # メモ内容を取得
    note = request.POST.get("note", "").strip()
    is_shared_value = request.POST.get("is_shared", "")
    is_shared = is_shared_value in ["on", "True", "true", "1"]

    # バリデーション
    if not note or len(note) < NoteSettings.MIN_NOTE_LENGTH:
        messages.error(
            request,
            f"メモは{NoteSettings.MIN_NOTE_LENGTH}文字以上で入力してください。",
        )
        return redirect("diary:teacher_student_detail", student_id=student_id)

    # メモを作成
    TeacherNote.objects.create(
        teacher=request.user,
        student=student,
        note=note,
        is_shared=is_shared,
    )

    shared_text = "（学年共有）" if is_shared else ""
    messages.success(
        request,
        f"{student.get_full_name()}さんの担任メモを追加しました{shared_text}",
    )

    return redirect("diary:teacher_student_detail", student_id=student_id)


@login_required
def teacher_edit_note(request, note_id):
    """担任メモ編集

    POSTリクエストで担任メモを編集する。
    権限チェック: メモ作成者のみ編集可能。
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    # メモを取得
    teacher_note = get_object_or_404(TeacherNote, id=note_id)

    # 作成者のみ編集可能
    if teacher_note.teacher != request.user:
        return HttpResponseForbidden("このメモを編集する権限がありません。")

    # メモ内容を取得
    note = request.POST.get("note", "").strip()
    is_shared_value = request.POST.get("is_shared", "")
    is_shared = is_shared_value in ["on", "True", "true", "1"]

    # バリデーション
    if not note or len(note) < NoteSettings.MIN_NOTE_LENGTH:
        messages.error(request, f"メモは{NoteSettings.MIN_NOTE_LENGTH}文字以上で入力してください。")
        return redirect("diary:teacher_student_detail", student_id=teacher_note.student.id)

    # メモを更新
    teacher_note.note = note
    teacher_note.is_shared = is_shared
    teacher_note.save()

    shared_text = "（学年共有）" if is_shared else ""
    messages.success(
        request,
        f"{teacher_note.student.get_full_name()}さんの担任メモを更新しました{shared_text}",
    )

    return redirect("diary:teacher_student_detail", student_id=teacher_note.student.id)


@login_required
def teacher_delete_note(request, note_id):
    """担任メモ削除

    POSTリクエストで担任メモを削除する。
    権限チェック: メモ作成者のみ削除可能。
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    # メモを取得
    teacher_note = get_object_or_404(TeacherNote, id=note_id)

    # 作成者チェック（他の担任が削除試行した場合は403）
    if teacher_note.teacher != request.user:
        return HttpResponseForbidden("このメモを削除する権限がありません。")

    student_id = teacher_note.student.id
    student_name = teacher_note.student.get_full_name()

    # メモを削除
    teacher_note.delete()

    messages.success(request, f"{student_name}さんの担任メモを削除しました。")

    return redirect("diary:teacher_student_detail", student_id=student_id)


class ClassHealthDashboardView(LoginRequiredMixin, TemplateView):
    """クラス健康状態ダッシュボード

    担任がクラス全体の体調・メンタル状態を一目で把握できるヒートマップ。
    受験前・テスト前の体調崩す生徒の早期発見、全体感の把握を実現。
    """

    template_name = "diary/class_health_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 期間パラメータ取得（デフォルト7日）
        # 設計判断: 7日/14日のみサポート（30日は視認性低下のため削除）
        # - 7日間: 日常的な振り返りに最適
        # - 14日間: 週次レポート、2週間の推移確認
        # - 30日間: 削除理由: ヒートマップセルが小さすぎてUI破綻、実務的にも不要
        days = int(self.request.GET.get("days", DashboardSettings.HEALTH_DASHBOARD_DEFAULT_DAYS))
        if days not in DashboardSettings.HEALTH_DASHBOARD_DAYS:
            days = (
                DashboardSettings.HEALTH_DASHBOARD_DEFAULT_DAYS
            )  # バリデーション（サポート外の日数はデフォルトにフォールバック）

        # 担当クラスを取得
        classroom = self.request.user.homeroom_classes.first()

        if not classroom:
            context["classroom"] = None
            context["students_matrix"] = []
            context["date_list"] = []
            context["summary"] = {}
            context["days"] = days
            return context

        # 日付範囲を計算
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days - 1)

        # 日付リスト生成（新しい順: 右から左）
        date_list = [start_date + timedelta(days=i) for i in range(days)]
        date_list.reverse()  # 新しい日付を右側に

        # データ取得（指定期間の連絡帳、N+1問題回避）
        entries = DiaryEntry.objects.filter(
            student__classes=classroom,
            entry_date__gte=start_date,
            entry_date__lte=end_date,
        ).select_related("student")

        # 生徒リスト取得
        students = classroom.students.all().order_by("last_name", "first_name")

        # 生徒×日付マトリクス生成
        students_matrix = []
        # 日付別サマリー辞書を初期化（日付ごとの体調・メンタル不調者数）
        daily_summary = {date: {"poor_health": 0, "poor_mental": 0} for date in date_list}
        poor_health_students = set()  # 体調不良者（health <= 2）
        poor_mental_students = set()  # メンタル低下者（mental <= 2）
        total_expected_entries = students.count() * days
        total_submitted_entries = 0

        for student in students:
            row = {"student": student, "entries": {}}

            # この生徒の連絡帳を日付別に格納
            student_entries = [e for e in entries if e.student_id == student.id]
            for entry in student_entries:
                row["entries"][entry.entry_date] = entry
                total_submitted_entries += 1

                # 体調・メンタル低下者をカウント（期間全体 + 日付別）
                if entry.health_condition <= HealthThresholds.POOR_CONDITION:
                    poor_health_students.add(student.id)
                    daily_summary[entry.entry_date]["poor_health"] += 1
                if entry.mental_condition <= HealthThresholds.POOR_CONDITION:
                    poor_mental_students.add(student.id)
                    daily_summary[entry.entry_date]["poor_mental"] += 1

            students_matrix.append(row)

        # サマリー統計計算
        submission_rate = (
            round(total_submitted_entries / total_expected_entries * 100, 1) if total_expected_entries > 0 else 0
        )

        summary = {
            "submission_rate": submission_rate,
            "poor_health_count": len(poor_health_students),
            "poor_mental_count": len(poor_mental_students),
            "total_students": students.count(),
            "days": days,
        }

        # 本日の日付を取得（欠席データ集計に使用）
        today = timezone.now().date()

        # 学年全体統計を計算（担任が学年平均と比較できるように）
        grade_classrooms = (
            ClassRoom.objects.filter(
                grade=classroom.grade,
                academic_year=classroom.academic_year,
            )
            .exclude(id=classroom.id)
            .prefetch_related("students")
        )

        if grade_classrooms.exists():
            # 学年全体（自分のクラスを除く）の統計
            # パフォーマンス最適化: 一括クエリで学年全体のデータを取得（2N回→2回、83-92%削減）
            grade_total_students = 0
            grade_poor_health_students = set()
            grade_poor_mental_students = set()

            # 学年全体の生徒リストを一括取得
            all_grade_students = []
            for other_classroom in grade_classrooms:
                other_students = list(other_classroom.students.all())
                all_grade_students.extend(other_students)
                grade_total_students += len(other_students)

            # 学年全体の連絡帳を一括取得（1回のクエリ）
            if all_grade_students:
                grade_entries = DiaryEntry.objects.filter(
                    student__in=all_grade_students,
                    entry_date__gte=start_date,
                    entry_date__lte=end_date,
                )

                # Pythonで集計（メモリ内処理）
                for entry in grade_entries:
                    if entry.health_condition <= HealthThresholds.POOR_CONDITION:
                        grade_poor_health_students.add(entry.student_id)
                    if entry.mental_condition <= HealthThresholds.POOR_CONDITION:
                        grade_poor_mental_students.add(entry.student_id)

            # 学年全体の本日の欠席者数を一括取得（1回のクエリ）
            grade_absent_today = DailyAttendance.objects.filter(
                classroom__in=grade_classrooms,
                date=today,
                status=AttendanceStatus.ABSENT,
            ).count()

            # 自クラスの本日の欠席者数を取得
            my_class_absent_today = DailyAttendance.objects.filter(
                classroom=classroom,
                date=today,
                status=AttendanceStatus.ABSENT,
            ).count()

            # 学年平均を計算（自分のクラスを含む全体）
            all_classrooms_count = grade_classrooms.count() + 1  # 自分のクラス含む
            grade_avg_poor_health = round(len(grade_poor_health_students) / grade_classrooms.count(), 1)
            grade_avg_poor_mental = round(len(grade_poor_mental_students) / grade_classrooms.count(), 1)
            grade_avg_absent_today = round(grade_absent_today / grade_classrooms.count(), 1)

            # 自クラスのデータ
            my_class_poor_health = summary["poor_health_count"]
            my_class_poor_mental = summary["poor_mental_count"]

            # 差分計算（自クラス - 学年平均）
            diff_poor_health = my_class_poor_health - grade_avg_poor_health
            diff_poor_mental = my_class_poor_mental - grade_avg_poor_mental
            diff_absent_today = my_class_absent_today - grade_avg_absent_today

            grade_summary = {
                "total_students": grade_total_students + summary["total_students"],
                "class_count": all_classrooms_count,
                "avg_poor_health": grade_avg_poor_health,
                "avg_poor_mental": grade_avg_poor_mental,
                "avg_absent_today": grade_avg_absent_today,
                # 自クラスのデータを追加
                "my_class_poor_health": my_class_poor_health,
                "my_class_poor_mental": my_class_poor_mental,
                "my_class_absent_today": my_class_absent_today,
                # 差分を追加
                "diff_poor_health": round(diff_poor_health, 1),
                "diff_poor_mental": round(diff_poor_mental, 1),
                "diff_absent_today": round(diff_absent_today, 1),
            }
        else:
            # クラスが1つしかない場合、自クラスのデータのみ表示
            # 本日の欠席者数を取得
            my_class_absent_today = DailyAttendance.objects.filter(
                classroom=classroom,
                date=today,
                status=AttendanceStatus.ABSENT,
            ).count()

            grade_summary = {
                "my_class_poor_health": summary["poor_health_count"],
                "my_class_poor_mental": summary["poor_mental_count"],
                "my_class_absent_today": my_class_absent_today,
                "single_class": True,  # テンプレートで判定用
            }

        # 本日の欠席者情報を集計（todayは既に794行目で取得済み）
        today_attendance = DailyAttendance.objects.filter(
            classroom=classroom,
            date=today,
        )
        total_absent = today_attendance.filter(status=AttendanceStatus.ABSENT).count()
        absent_illness = today_attendance.filter(
            status=AttendanceStatus.ABSENT,
            absence_reason=AbsenceReason.ILLNESS,
        ).count()

        absence_summary = {
            "total_absent": total_absent,
            "absent_illness": absent_illness,
        }

        # アラート生成（閾値を5名に変更: MAP-2Aの2段階アラートと整合）
        alerts = []
        if summary["poor_health_count"] >= HealthThresholds.CLASS_ALERT_THRESHOLD:
            alerts.append(
                f"⚠️ 体調不良者が{summary['poor_health_count']}名います。クラス全体の健康状態に注意が必要です。",
            )
        if summary["poor_mental_count"] >= HealthThresholds.CLASS_ALERT_THRESHOLD:
            alerts.append(
                f"💙 メンタル低下者が{summary['poor_mental_count']}名います。声かけやフォローを検討してください。",
            )
        if submission_rate < DashboardSettings.SUBMISSION_RATE_WARNING:
            alerts.append(
                f"📝 提出率が{submission_rate}%です。未提出者への声かけをお願いします。",
            )

        context["classroom"] = classroom
        context["absence_summary"] = absence_summary
        context["students_matrix"] = students_matrix
        context["date_list"] = date_list
        context["daily_summary"] = daily_summary
        context["summary"] = summary
        context["grade_summary"] = grade_summary
        context["alerts"] = alerts
        context["days"] = days

        return context


class GradeOverviewView(LoginRequiredMixin, TemplateView):
    """学年主任用ダッシュボード（学年全体の比較）"""

    template_name = "diary/grade_overview.html"

    def dispatch(self, request, *args, **kwargs):
        # grade_leaderまたはスーパーユーザーのみアクセス可能
        if not request.user.is_superuser and request.user.profile.role != "grade_leader":
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        managed_grade = user.profile.managed_grade

        # 同じ学年の全クラスを取得
        classrooms = ClassRoom.objects.filter(
            grade=managed_grade,
            academic_year=2025,
        ).prefetch_related("students")

        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # クラスごとの統計
        classroom_stats = []
        for classroom in classrooms:
            students = classroom.students.all()
            student_count = students.count()

            # 過去7日間の連絡帳
            entries = DiaryEntry.objects.filter(
                student__in=students,
                entry_date__gte=week_ago,
                entry_date__lte=today,
            )

            # 本日の出席記録
            today_attendance = DailyAttendance.objects.filter(
                classroom=classroom,
                date=today,
            )
            absent_count = today_attendance.filter(
                status=AttendanceStatus.ABSENT,
            ).count()
            absent_illness = today_attendance.filter(
                status=AttendanceStatus.ABSENT,
                absence_reason=AbsenceReason.ILLNESS,
            ).count()

            # 統計計算
            total_entries = entries.count()
            expected_entries = student_count * 7
            submission_rate = round((total_entries / expected_entries * 100), 1) if expected_entries > 0 else 0

            poor_health_count = (
                entries.filter(health_condition__lte=HealthThresholds.POOR_CONDITION)
                .values("student")
                .distinct()
                .count()
            )
            poor_mental_count = (
                entries.filter(mental_condition__lte=HealthThresholds.POOR_CONDITION)
                .values("student")
                .distinct()
                .count()
            )

            # 警告レベル判定
            alert_level = "success"  # 緑
            if (
                absent_illness >= HealthThresholds.CLASS_ALERT_THRESHOLD
                or poor_health_count >= HealthThresholds.CLASS_ALERT_THRESHOLD
            ):
                alert_level = "danger"  # 赤
            elif (
                absent_illness >= HealthThresholds.CONSECUTIVE_DAYS
                or poor_health_count >= HealthThresholds.CONSECUTIVE_DAYS
            ):
                alert_level = "warning"  # 黄

            classroom_stats.append(
                {
                    "classroom": classroom,
                    "student_count": student_count,
                    "submission_rate": submission_rate,
                    "absent_count": absent_count,
                    "absent_illness": absent_illness,
                    "poor_health_count": poor_health_count,
                    "poor_mental_count": poor_mental_count,
                    "alert_level": alert_level,
                },
            )

        # 学年全体サマリー
        total_students = sum(s["student_count"] for s in classroom_stats)
        avg_submission_rate = (
            round(sum(s["submission_rate"] for s in classroom_stats) / len(classroom_stats), 1)
            if classroom_stats
            else 0
        )
        total_absent = sum(s["absent_count"] for s in classroom_stats)
        total_absent_illness = sum(s["absent_illness"] for s in classroom_stats)
        total_poor_health = sum(s["poor_health_count"] for s in classroom_stats)
        total_poor_mental = sum(s["poor_mental_count"] for s in classroom_stats)

        context["managed_grade"] = managed_grade
        context["classroom_stats"] = classroom_stats
        context["summary"] = {
            "total_students": total_students,
            "class_count": len(classroom_stats),
            "avg_submission_rate": avg_submission_rate,
            "total_absent": total_absent,
            "total_absent_illness": total_absent_illness,
            "total_poor_health": total_poor_health,
            "total_poor_mental": total_poor_mental,
        }

        # アラート生成（MAP-2A: 学年主任向け早期警告システム）
        escalation_alerts = []

        # 全クラスの全生徒をチェック（Level 2: メンタル★1が3日連続 → 学年主任通知）
        for classroom_stat in classroom_stats:
            classroom = classroom_stat["classroom"]
            for student in classroom.students.all():
                # 過去3日分のエントリーを取得
                recent_entries = student.diary_entries.order_by("-entry_date")[:3]

                # 3件揃っているか、かつ全てメンタル★1かチェック
                if len(recent_entries) == 3 and all(entry.mental_condition == 1 for entry in recent_entries):
                    escalation_alerts.append(
                        {
                            "level": "critical_escalation",
                            "student": student,
                            "classroom": classroom,
                            "teacher": classroom.homeroom_teacher,
                            "message": f"【学年主任通知】{classroom}組 {student.get_full_name()}さん - メンタル★1が3日連続",
                            "dates": [entry.entry_date for entry in reversed(recent_entries)],
                            "action": "担任に状況を確認し、保護者面談や専門機関との連携を検討してください。",
                        },
                    )

        context["escalation_alerts"] = escalation_alerts

        return context


class SchoolOverviewView(LoginRequiredMixin, TemplateView):
    """校長/教頭用ダッシュボード（学校全体の把握）"""

    template_name = "diary/school_overview.html"

    def dispatch(self, request, *args, **kwargs):
        # school_leaderまたはスーパーユーザーのみアクセス可能
        if not request.user.is_superuser and request.user.profile.role != "school_leader":
            msg = "校長/教頭権限が必要です。"
            raise PermissionDenied(msg)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 全学年の統計
        grade_stats = []
        for grade in [GradeLevel.GRADE_1, GradeLevel.GRADE_2, GradeLevel.GRADE_3]:
            classrooms = ClassRoom.objects.filter(
                grade=grade,
                academic_year=2025,
            ).prefetch_related("students")

            all_students = []
            for classroom in classrooms:
                all_students.extend(list(classroom.students.all()))

            student_count = len(all_students)

            today = timezone.now().date()
            week_ago = today - timedelta(days=7)

            # 過去7日間の連絡帳
            entries = DiaryEntry.objects.filter(
                student__in=all_students,
                entry_date__gte=week_ago,
                entry_date__lte=today,
            )

            # 本日の出席記録
            today_attendance = DailyAttendance.objects.filter(
                classroom__in=classrooms,
                date=today,
            )
            absent_count = today_attendance.filter(
                status=AttendanceStatus.ABSENT,
            ).count()
            absent_illness = today_attendance.filter(
                status=AttendanceStatus.ABSENT,
                absence_reason=AbsenceReason.ILLNESS,
            ).count()

            # 欠席率計算
            absence_rate = round((absent_count / student_count * 100), 1) if student_count > 0 else 0

            # 統計計算
            total_entries = entries.count()
            expected_entries = student_count * 7
            submission_rate = round((total_entries / expected_entries * 100), 1) if expected_entries > 0 else 0

            poor_health_count = (
                entries.filter(health_condition__lte=HealthThresholds.POOR_CONDITION)
                .values("student")
                .distinct()
                .count()
            )
            poor_mental_count = (
                entries.filter(mental_condition__lte=HealthThresholds.POOR_CONDITION)
                .values("student")
                .distinct()
                .count()
            )

            # 警告レベル判定（学級閉鎖基準: 20%）
            alert_level = "success"  # 緑
            if absence_rate >= 15:  # 15%以上
                alert_level = "danger"  # 赤
            elif absence_rate >= 10:  # 10%以上
                alert_level = "warning"  # 黄

            grade_stats.append(
                {
                    "grade": grade,
                    "grade_display": f"{grade}年",
                    "class_count": classrooms.count(),
                    "student_count": student_count,
                    "submission_rate": submission_rate,
                    "absent_count": absent_count,
                    "absent_illness": absent_illness,
                    "absence_rate": absence_rate,
                    "poor_health_count": poor_health_count,
                    "poor_mental_count": poor_mental_count,
                    "alert_level": alert_level,
                },
            )

        # 学校全体サマリー
        total_students = sum(s["student_count"] for s in grade_stats)
        total_absent = sum(s["absent_count"] for s in grade_stats)
        total_absent_illness = sum(s["absent_illness"] for s in grade_stats)
        total_poor_health = sum(s["poor_health_count"] for s in grade_stats)
        total_poor_mental = sum(s["poor_mental_count"] for s in grade_stats)
        avg_submission_rate = round(sum(s["submission_rate"] for s in grade_stats) / 3, 1) if grade_stats else 0

        # 全体の警告レベル
        school_alert_level = "success"
        if any(s["alert_level"] == "danger" for s in grade_stats):
            school_alert_level = "danger"
        elif any(s["alert_level"] == "warning" for s in grade_stats):
            school_alert_level = "warning"

        context["grade_stats"] = grade_stats
        context["summary"] = {
            "total_students": total_students,
            "avg_submission_rate": avg_submission_rate,
            "total_absent": total_absent,
            "total_absent_illness": total_absent_illness,
            "total_poor_health": total_poor_health,
            "total_poor_mental": total_poor_mental,
            "school_alert_level": school_alert_level,
        }

        return context


@login_required
def teacher_save_attendance(request):
    """担任が本日の出席データを保存"""
    if request.method != "POST":
        return redirect("diary:teacher_dashboard")

    # 担任のクラスルームを取得
    classroom = request.user.homeroom_classes.first()
    if not classroom:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "message": "担任権限がありません"})
        messages.error(request, "担任権限がありません")
        return redirect("diary:teacher_dashboard")

    # AJAXリクエストの場合は単一生徒データ（student_id, date, status）
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        student_id = request.POST.get("student_id")
        date_str = request.POST.get("date")
        status = request.POST.get("status")

        # バリデーション
        if not student_id or not date_str or not status:
            return JsonResponse({"status": "error", "message": "必須パラメータが不足しています"})

        # 生徒が自分のクラスに所属しているか確認
        if not classroom.students.filter(id=student_id).exists():
            return JsonResponse({"status": "error", "message": "生徒が見つかりません"})

        from datetime import date as dt_date

        student = User.objects.get(id=student_id)
        date = dt_date.fromisoformat(date_str)

        # DailyAttendanceレコードを更新または作成
        DailyAttendance.objects.update_or_create(
            student=student,
            classroom=classroom,
            date=date,
            defaults={
                "status": status,
                "noted_by": request.user,
            },
        )

        return JsonResponse({"status": "success", "message": "出席データを保存しました"})

    # 通常のフォームリクエスト（複数生徒一括）
    today = timezone.now().date()

    # POSTデータから出席状況を取得（student_id_status, student_id_reason形式）
    for key, value in request.POST.items():
        if key.startswith("student_") and key.endswith("_status"):
            student_id = int(key.replace("student_", "").replace("_status", ""))

            # 生徒が自分のクラスに所属しているか確認
            if not classroom.students.filter(id=student_id).exists():
                continue

            student = User.objects.get(id=student_id)
            status = value

            # 欠席理由を取得（欠席の場合のみ）
            absence_reason = None
            if status == AttendanceStatus.ABSENT:
                reason_key = f"student_{student_id}_reason"
                absence_reason = request.POST.get(reason_key)

            # DailyAttendanceレコードを更新または作成
            DailyAttendance.objects.update_or_create(
                student=student,
                classroom=classroom,
                date=today,
                defaults={
                    "status": status,
                    "absence_reason": absence_reason,
                    "noted_by": request.user,
                },
            )

    messages.success(request, f"{today.strftime('%Y年%m月%d日')}の出席データを保存しました")
    return redirect("diary:teacher_dashboard")


@login_required
def mark_shared_note_read(request, note_id):
    """学年共有アラートの既読処理

    POSTリクエストで共有メモを既読にする。
    権限チェック: 共有メモ（is_shared=True）のみ既読可能。
    セキュリティ: 自分が作成したメモは既読にできない。
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    # 共有メモを取得（is_shared=Trueのみ）
    note = get_object_or_404(TeacherNote, id=note_id, is_shared=True)

    # 自分が作成したメモは既読にできない
    if note.teacher == request.user:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"status": "error", "message": "自分が作成したメモは既読にできません。"})
        messages.warning(request, "自分が作成したメモは既読にできません。")
        return redirect("diary:teacher_dashboard")

    # 既読状態を作成（冪等性保証）
    TeacherNoteReadStatus.objects.get_or_create(
        teacher=request.user,
        note=note,
    )

    student_name = note.student.get_full_name()

    # AJAXリクエストの場合はJSON返却
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"status": "success", "message": f"{student_name}さんの共有メモを既読にしました。"})

    messages.success(request, f"{student_name}さんの共有メモを既読にしました。")
    return redirect("diary:teacher_dashboard")


@login_required
def password_change_view(request):
    """パスワード変更ビュー（初回ログイン時用）

    仮パスワードから本パスワードへの変更を行う。
    変更成功後、requires_password_changeをFalseに設定し、
    メールアドレスを認証済みにする。
    """
    from django.contrib.auth import update_session_auth_hash

    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            # セッションを維持（パスワード変更後もログイン状態を保持）
            update_session_auth_hash(request, user)
            messages.success(request, "✅ パスワード変更が完了しました。メール認証も完了しました。")
            # 役割別ダッシュボードへリダイレクト
            return redirect("home")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, "diary/password_change.html", {"form": form})


@login_required
def teacher_mark_as_read_quick(request, diary_id):
    """カードから既読のみ（AJAX用）

    POSTリクエストで連絡帳を既読にする。
    action_status=NOT_REQUIREDを設定（対応不要）。
    権限チェック: 担任が自分のクラスの生徒の連絡帳のみ操作可能。

    Returns:
        JsonResponse: {'status': 'success'/'error', 'message': '...'}
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POSTリクエストのみ許可"}, status=405)

    # 担任のクラスを取得
    classroom = request.user.homeroom_classes.first()
    if not classroom:
        return JsonResponse({"status": "error", "message": "権限がありません"}, status=403)

    # 連絡帳を取得
    diary = get_object_or_404(DiaryEntry, id=diary_id)

    # クラスの生徒のもののみアクセス可能
    if diary.student not in classroom.students.all():
        return JsonResponse({"status": "error", "message": "このクラスの生徒の連絡帳ではありません"}, status=403)

    # 既読処理
    diary.is_read = True
    diary.read_by = request.user
    diary.read_at = timezone.now()

    # 既読時に「📖 読んだよ」を自動設定
    diary.public_reaction = PublicReaction.CHECKED

    # action_status = NOT_REQUIRED（対応不要）
    diary.action_status = ActionStatus.NOT_REQUIRED

    diary.save()

    return JsonResponse({"status": "success", "message": "既読にしました"})


@login_required
def teacher_create_task_from_card(request, diary_id):
    """カードからタスク化（AJAX用）

    POSTリクエストで連絡帳を既読にし、タスク化する。
    action_status=IN_PROGRESSを設定。
    権限チェック: 担任が自分のクラスの生徒の連絡帳のみ操作可能。

    Request POST data:
        internal_action: 要対応内容（parent_contact, health_check, counseling, home_visit, meeting_needed）

    Returns:
        JsonResponse: {'status': 'success'/'error', 'message': '...'}
    """
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POSTリクエストのみ許可"}, status=405)

    # 担任のクラスを取得
    classroom = request.user.homeroom_classes.first()
    if not classroom:
        return JsonResponse({"status": "error", "message": "権限がありません"}, status=403)

    # 連絡帳を取得
    diary = get_object_or_404(DiaryEntry, id=diary_id)

    # クラスの生徒のもののみアクセス可能
    if diary.student not in classroom.students.all():
        return JsonResponse({"status": "error", "message": "このクラスの生徒の連絡帳ではありません"}, status=403)

    # JSON dataからinternal_actionを取得
    try:
        data = json.loads(request.body)
        internal_action = data.get("internal_action")
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"status": "error", "message": "不正なリクエストです"}, status=400)

    if not internal_action:
        return JsonResponse({"status": "error", "message": "internal_actionが必要です"}, status=400)

    # 既読処理
    diary.is_read = True
    diary.read_by = request.user
    diary.read_at = timezone.now()

    # 既読時に「📖 読んだよ」を自動設定
    diary.public_reaction = PublicReaction.CHECKED

    # タスク化
    diary.internal_action = internal_action
    diary.action_status = ActionStatus.IN_PROGRESS

    diary.save()

    return JsonResponse({"status": "success", "message": "タスク化しました"})


def health_check(request):
    """ALB Health Check endpoint

    Returns HTTP 200 with JSON status for AWS Application Load Balancer health checks.
    This endpoint does not require authentication.
    """
    return JsonResponse({"status": "healthy"})


@login_required
def trigger_test_data_generation(request):
    """テストデータ生成を手動でトリガーする（管理者専用）

    SSM Run Commandを使用してEC2インスタンス上のDjangoコマンドを実行します。
    Superuserのみがアクセス可能です。
    """
    # Superuserチェック
    if not request.user.is_superuser:
        msg = "管理者のみがアクセス可能です"
        raise PermissionDenied(msg)

    # GETリクエスト
    if request.method == "GET":
        return render(request, "diary/admin/generate_test_data_confirm.html")

    # POSTリクエスト
    if request.method == "POST":
        import boto3
        from django.conf import settings

        try:
            # SSM Clientを作成
            ssm_client = boto3.client("ssm", region_name=settings.AWS_REGION)

            # EC2インスタンスID
            instance_id = settings.EC2_INSTANCE_ID

            # 実行するコマンド
            command = (
                "cd /home/ubuntu/school_diary && "
                "docker compose -f docker-compose.production.yml exec -T django "
                "python manage.py create_production_test_data"
            )

            # SSM Run Commandを実行
            response = ssm_client.send_command(
                InstanceIds=[instance_id],
                DocumentName="AWS-RunShellScript",
                Parameters={"commands": [command]},
                Comment="Manual test data generation triggered from Django admin",
            )

            command_id = response["Command"]["CommandId"]

            messages.success(
                request,
                f"テストデータ生成を開始しました。コマンドID: {command_id}",
            )
            return redirect("admin:index")

        except Exception as e:
            messages.error(request, f"エラーが発生しました: {e!s}")
            return redirect("admin:index")

    return HttpResponseNotAllowed(["GET", "POST"])

"""Views for diary app."""

from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.db.models import Prefetch
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView
from django.views.generic import ListView
from django.views.generic import TemplateView
from django.views.generic import UpdateView

from .forms import DiaryEntryForm
from .models import AbsenceReason
from .models import ActionStatus
from .models import AttendanceStatus
from .models import ClassRoom
from .models import DailyAttendance
from .models import DiaryEntry
from .models import InternalAction
from .models import TeacherNote


def get_students_with_consecutive_decline(classroom, days=3, threshold=2):
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
    entries = DiaryEntry.objects.filter(
        student__classes=classroom,
        entry_date__gte=start_date,
        entry_date__lte=end_date,
    ).select_related("student").order_by("student", "-entry_date")

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
        context["recent_entries"] = (
            DiaryEntry.objects.filter(student=self.request.user)
            .select_related("read_by")
            .order_by("-entry_date")[:7]
        )

        # 今日の提出済みか確認（前登校日ベース）
        from .utils import get_previous_school_day

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
                "no_reaction_count": 0,
            }
            context["filter_type"] = "all"
            return context

        # サマリー統計を一括計算（最適化: 1つのクエリで全て集計）
        summary_stats = DiaryEntry.objects.filter(
            student__classes=classroom,
        ).aggregate(
            unread_total=Count("id", filter=Q(is_read=False)),
            pending_action_count=Count(
                "id",
                filter=Q(
                    internal_action__isnull=False,
                    action_status=ActionStatus.PENDING,
                ),
            ),
            urgent_action_count=Count(
                "id",
                filter=Q(internal_action=InternalAction.URGENT),
            ),
            no_reaction_count=Count(
                "id",
                filter=Q(
                    is_read=True,
                    public_reaction__isnull=True,
                ),
            ),
        )

        # 生徒一覧を取得（未読件数をアノテーション、N+1回避）
        students = (
            classroom.students.annotate(
                unread_count=Count(
                    "diary_entries",
                    filter=Q(diary_entries__is_read=False),
                ),
            )
            .prefetch_related(
                Prefetch(
                    "diary_entries",
                    queryset=DiaryEntry.objects.select_related(
                        "action_completed_by",
                    ).order_by("-entry_date")[:1],
                    to_attr="latest_entry_list",
                ),
            )
            .order_by("last_name", "first_name")
        )

        # テンプレート用にデータ整形
        student_data = []

        for student in students:
            latest_entry = (
                student.latest_entry_list[0] if student.latest_entry_list else None
            )
            student_data.append(
                {
                    "student": student,
                    "unread_count": student.unread_count,
                    "latest_entry": latest_entry,
                },
            )

        # フィルタ処理
        today = timezone.now().date()
        filter_type = self.request.GET.get("filter", "all")

        if filter_type == "urgent":
            # 緊急対応必要のみ
            student_data = [
                s
                for s in student_data
                if s["latest_entry"]
                and s["latest_entry"].internal_action == InternalAction.URGENT
            ]
        elif filter_type == "pending_action":
            # 未対応アクションのみ
            student_data = [
                s
                for s in student_data
                if s["latest_entry"]
                and s["latest_entry"].internal_action
                and s["latest_entry"].action_status == ActionStatus.PENDING
            ]
        elif filter_type == "unread":
            # 未読のみ
            student_data = [s for s in student_data if s["unread_count"] > 0]
        elif filter_type == "no_reaction":
            # 反応未選択のみ
            student_data = [
                s
                for s in student_data
                if s["latest_entry"] and not s["latest_entry"].public_reaction
            ]
        elif filter_type == "absent":
            # 欠席者のみ（今日欠席している生徒）
            absent_records = DailyAttendance.objects.filter(
                classroom=classroom,
                date=today,
                status=AttendanceStatus.ABSENT,
            ).select_related("student")

            # 欠席者の生徒データを作成
            absent_student_data = []
            for record in absent_records:
                # 最新の連絡帳を取得
                latest_entry = DiaryEntry.objects.filter(
                    student=record.student,
                ).order_by("-entry_date").first()

                absent_student_data.append({
                    "student": record.student,
                    "latest_entry": latest_entry,
                    "unread_count": 0,  # 欠席者なので未読カウントは不要
                    "absence_reason": record.absence_reason,  # 欠席理由を追加
                })

            student_data = absent_student_data
        elif filter_type == "no_entry_yesterday":
            # 昨日未提出のみ
            yesterday = today - timedelta(days=1)

            no_entry_student_data = []
            for student in classroom.students.all():
                # 昨日の連絡帳があるかチェック
                has_entry = DiaryEntry.objects.filter(
                    student=student,
                    entry_date=yesterday,
                ).exists()

                if not has_entry:
                    # 最新の連絡帳を取得
                    latest_entry = DiaryEntry.objects.filter(
                        student=student,
                    ).order_by("-entry_date").first()

                    no_entry_student_data.append({
                        "student": student,
                        "latest_entry": latest_entry,
                        "unread_count": 0,
                    })

            student_data = no_entry_student_data

        context["classroom"] = classroom
        context["students"] = student_data
        context["today"] = today
        context["summary"] = {
            "unread_total": summary_stats["unread_total"],
            "pending_action_count": summary_stats["pending_action_count"],
            "urgent_action_count": summary_stats["urgent_action_count"],
            "no_reaction_count": summary_stats["no_reaction_count"],
        }
        context["filter_type"] = filter_type

        # 本日の欠席者情報を集計
        today_attendance = DailyAttendance.objects.filter(
            classroom=classroom,
            date=today,
        )
        absent_students = []
        for attendance in today_attendance.filter(status=AttendanceStatus.ABSENT).select_related("student"):
            absent_students.append({
                "student": attendance.student,
                "absence_reason": attendance.get_absence_reason_display() if attendance.absence_reason else "未設定",
                "absence_reason_code": attendance.absence_reason,
            })

        absence_data = {
            "total_absent": len(absent_students),
            "absent_illness": today_attendance.filter(
                status=AttendanceStatus.ABSENT,
                absence_reason=AbsenceReason.ILLNESS,
            ).count(),
            "absent_students": absent_students,
        }
        context["absence_data"] = absence_data

        # 全生徒リスト（出席入力モーダル用）
        context["all_students"] = classroom.students.all().order_by("last_name", "first_name")

        # アラート生成（MAP-2A: 早期警告システム）
        from .utils import check_consecutive_decline, check_critical_mental_state, get_previous_school_day

        alerts = []

        # 全生徒をチェック（フィルタに依存しない早期警告）
        for student in classroom.students.all():
            # Level 1: Critical - メンタル★1（即座の対応が必要）
            mental_state = check_critical_mental_state(student)
            if mental_state["has_alert"]:
                alerts.append({
                    "level": "critical",
                    "type": "mental_critical",
                    "student": student,
                    "message": f"{student.get_full_name()}さん - メンタル★1",
                    "date": mental_state["date"],
                    "action": "声をかけてください。",
                })

            # Level 3: Warning - メンタル3日連続低下
            mental_decline = check_consecutive_decline(student, "mental_condition")
            if mental_decline["has_alert"]:
                trend_values = mental_decline["trend"]
                trend_str = " → ".join([f"★{'★' * v}" for v in trend_values])
                alerts.append({
                    "level": "warning",
                    "type": "mental_decline",
                    "student": student,
                    "message": f"{student.get_full_name()}さん - メンタル低下が続いています",
                    "trend": trend_str,
                    "dates": mental_decline["dates"],
                    "action": "注意して見守ってください。",
                })

        # Level 4: Warning - クラス5人以上が体調不良
        previous_date = get_previous_school_day(today)
        poor_health_count = DiaryEntry.objects.filter(
            student__classes=classroom,
            entry_date=previous_date,
            health_condition__lte=2,
        ).count()

        if poor_health_count >= 5:
            alerts.append({
                "level": "warning",
                "type": "class_health",
                "message": f"クラス全体 - 体調不良が多いです（{poor_health_count}名）",
                "date": previous_date,
                "action": "注意してください。",
            })

        context["alerts"] = alerts

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

    def get_queryset(self):
        """セキュリティ: 自分の未既読エントリーのみ編集可能

        フィルタ条件:
        - student=self.request.user: 自分のエントリーのみ
        - is_read=False: 既読前のみ（is_editable=True）

        既読後または他人のエントリーにアクセスした場合は404エラー。
        """
        return DiaryEntry.objects.filter(
            student=self.request.user,
            is_read=False,  # is_editable = True
        )

    def form_valid(self, form):
        """フォーム送信時の処理

        編集成功メッセージを表示。
        """
        messages.success(self.request, "連絡帳を更新しました。")
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
            from django.contrib.auth import get_user_model

            User = get_user_model()
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
            notes = TeacherNote.objects.filter(
                student=student,
            ).filter(
                Q(is_shared=True) | Q(teacher=self.request.user),
            ).select_related("teacher").order_by("-updated_at")
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

    # 連絡帳を取得（クラスの生徒のもののみ）
    diary = get_object_or_404(
        DiaryEntry,
        id=diary_id,
        student__classes=classroom,
    )

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
            # 対応記録が削除された場合、ステータスもクリア
            diary.action_status = None

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

    # ダッシュボードまたは生徒詳細ページにリダイレクト
    # リファラーを確認して適切にリダイレクト
    referer = request.META.get("HTTP_REFERER", "")
    if "teacher/student/" in referer:
        return redirect("diary:teacher_student_detail", student_id=diary.student.id)
    return redirect("diary:teacher_dashboard")


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
    from .adapters import RoleBasedRedirectAdapter

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
    from django.contrib.auth import get_user_model
    User = get_user_model()
    student = get_object_or_404(User, id=student_id, classes=classroom)

    # メモ内容を取得
    note = request.POST.get("note", "").strip()
    is_shared = request.POST.get("is_shared") == "on"

    # バリデーション
    if not note or len(note) < 10:
        messages.error(request, "メモは10文字以上で入力してください。")
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

    # メモを取得（作成者のみ編集可能）
    teacher_note = get_object_or_404(TeacherNote, id=note_id, teacher=request.user)

    # メモ内容を取得
    note = request.POST.get("note", "").strip()
    is_shared = request.POST.get("is_shared") == "on"

    # バリデーション
    if not note or len(note) < 10:
        messages.error(request, "メモは10文字以上で入力してください。")
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

    # メモを取得（作成者のみ削除可能）
    teacher_note = get_object_or_404(TeacherNote, id=note_id, teacher=request.user)
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
        days = int(self.request.GET.get("days", 7))
        if days not in [7, 14]:
            days = 7  # バリデーション（7日/14日以外は7日にフォールバック）

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
            student__classes=classroom, entry_date__gte=start_date, entry_date__lte=end_date,
        ).select_related("student")

        # 生徒リスト取得
        students = classroom.students.all().order_by("last_name", "first_name")

        # 生徒×日付マトリクス生成
        students_matrix = []
        # 日付別サマリー辞書を初期化（日付ごとの体調・メンタル不調者数）
        daily_summary = {
            date: {"poor_health": 0, "poor_mental": 0} for date in date_list
        }
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
                if entry.health_condition <= 2:
                    poor_health_students.add(student.id)
                    daily_summary[entry.entry_date]["poor_health"] += 1
                if entry.mental_condition <= 2:
                    poor_mental_students.add(student.id)
                    daily_summary[entry.entry_date]["poor_mental"] += 1

            students_matrix.append(row)

        # サマリー統計計算
        submission_rate = (
            round(total_submitted_entries / total_expected_entries * 100, 1)
            if total_expected_entries > 0
            else 0
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
        grade_classrooms = ClassRoom.objects.filter(
            grade=classroom.grade,
            academic_year=classroom.academic_year,
        ).exclude(id=classroom.id).prefetch_related('students')

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
                    if entry.health_condition <= 2:
                        grade_poor_health_students.add(entry.student_id)
                    if entry.mental_condition <= 2:
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
        if summary["poor_health_count"] >= 5:
            alerts.append(
                f"⚠️ 体調不良者が{summary['poor_health_count']}名います。クラス全体の健康状態に注意が必要です。",
            )
        if summary["poor_mental_count"] >= 5:
            alerts.append(
                f"💙 メンタル低下者が{summary['poor_mental_count']}名います。声かけやフォローを検討してください。",
            )
        if submission_rate < 80:
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
        # grade_leaderのみアクセス可能
        if request.user.profile.role != "grade_leader":
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
            submission_rate = (
                round((total_entries / expected_entries * 100), 1)
                if expected_entries > 0
                else 0
            )

            poor_health_count = (
                entries.filter(health_condition__lte=2).values("student").distinct().count()
            )
            poor_mental_count = (
                entries.filter(mental_condition__lte=2).values("student").distinct().count()
            )

            # 警告レベル判定
            alert_level = "success"  # 緑
            if absent_illness >= 5 or poor_health_count >= 5:
                alert_level = "danger"  # 赤
            elif absent_illness >= 3 or poor_health_count >= 3:
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
                if len(recent_entries) == 3 and all(
                    entry.mental_condition == 1 for entry in recent_entries
                ):
                    escalation_alerts.append({
                        "level": "critical_escalation",
                        "student": student,
                        "classroom": classroom,
                        "teacher": classroom.homeroom_teacher,
                        "message": f"【学年主任通知】{classroom}組 {student.get_full_name()}さん - メンタル★1が3日連続",
                        "dates": [entry.entry_date for entry in reversed(recent_entries)],
                        "action": "担任に状況を確認し、保護者面談や専門機関との連携を検討してください。",
                    })

        context["escalation_alerts"] = escalation_alerts

        return context


class SchoolOverviewView(LoginRequiredMixin, TemplateView):
    """校長/教頭用ダッシュボード（学校全体の把握）"""

    template_name = "diary/school_overview.html"

    def dispatch(self, request, *args, **kwargs):
        # school_leaderのみアクセス可能
        if request.user.profile.role != "school_leader":
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 全学年の統計
        grade_stats = []
        for grade in [1, 2, 3]:
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
            absence_rate = (
                round((absent_count / student_count * 100), 1) if student_count > 0 else 0
            )

            # 統計計算
            total_entries = entries.count()
            expected_entries = student_count * 7
            submission_rate = (
                round((total_entries / expected_entries * 100), 1)
                if expected_entries > 0
                else 0
            )

            poor_health_count = (
                entries.filter(health_condition__lte=2).values("student").distinct().count()
            )
            poor_mental_count = (
                entries.filter(mental_condition__lte=2).values("student").distinct().count()
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
        avg_submission_rate = (
            round(sum(s["submission_rate"] for s in grade_stats) / 3, 1)
            if grade_stats
            else 0
        )

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
        messages.error(request, "担任権限がありません")
        return redirect("diary:teacher_dashboard")

    today = timezone.now().date()

    # POSTデータから出席状況を取得（student_id_status, student_id_reason形式）
    from django.contrib.auth import get_user_model
    User = get_user_model()

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

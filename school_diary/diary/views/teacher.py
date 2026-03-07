"""Teacher views - dashboard, mark-as-read, notes, attendance."""

import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.http import HttpResponseNotAllowed
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic import TemplateView

from ..services import alert_service
from ..constants import HealthThresholds
from ..constants import NoteSettings
from ..models import ActionStatus
from ..models import AttendanceStatus
from ..models import DailyAttendance
from ..models import DiaryEntry
from ..models import PublicReaction
from ..models import TeacherNote
from ..models import TeacherNoteReadStatus
from ..services.teacher_dashboard_service import TeacherDashboardService
from ..utils import check_consecutive_decline
from ..utils import check_critical_mental_state
from ..utils import get_previous_school_day

User = get_user_model()

__all__ = [
    "TeacherDashboardView",
    "TeacherStudentDetailView",
    "teacher_mark_as_read",
    "teacher_mark_as_read_quick",
    "teacher_mark_action_completed",
    "teacher_create_task_from_card",
    "teacher_add_note",
    "teacher_edit_note",
    "teacher_delete_note",
    "mark_shared_note_read",
    "teacher_save_attendance",
]


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

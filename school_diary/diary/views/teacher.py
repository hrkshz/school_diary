"""Teacher views - dashboard, mark-as-read, notes, attendance."""

import json

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import Http404
from django.http import HttpResponseNotAllowed
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import ListView
from django.views.generic import TemplateView

from ..models import AttendanceStatus
from ..models import DailyAttendance
from ..models import DiaryEntry
from ..models import TeacherNote
from ..authorization import can_access_student
from ..authorization import get_primary_classroom
from ..services.diary_entry_service import DiaryEntryService
from ..services.diary_entry_service import UNSET
from ..services.teacher_note_service import TeacherNoteService
from ..services.teacher_dashboard_service import TeacherDashboardService

User = get_user_model()

__all__ = [
    "TeacherDashboardView",
    "TeacherStudentDetailView",
    "mark_shared_note_read",
    "teacher_add_note",
    "teacher_create_task_from_card",
    "teacher_delete_note",
    "teacher_edit_note",
    "teacher_mark_action_completed",
    "teacher_mark_as_read",
    "teacher_mark_as_read_quick",
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
        context.update(TeacherDashboardService.get_dashboard_data(self.request.user))
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
        classroom = get_primary_classroom(self.request.user)
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
        student = get_object_or_404(User, id=student_id)
        if not can_access_student(self.request.user, student):
            raise Http404
        context["student"] = student
        context["unread_count"] = DiaryEntry.objects.filter(student=student, is_read=False).count()
        context["notes"] = (
            TeacherNote.objects.filter(student=student)
            .filter(Q(is_shared=True) | Q(teacher=self.request.user))
            .select_related("teacher")
            .order_by("-updated_at")
        )

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
    classroom = get_primary_classroom(request.user)
    if not classroom:
        raise PermissionDenied("担任権限がありません。")

    diary = get_object_or_404(DiaryEntry, id=diary_id, student__classes=classroom)

    # 既読状態を記録
    was_already_read = diary.is_read

    DiaryEntryService.mark_read(
        diary,
        request.user,
        reaction=request.POST.get("public_reaction", "").strip() if "public_reaction" in request.POST else UNSET,
        action=request.POST.get("internal_action", "").strip() if "internal_action" in request.POST else UNSET,
    )

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
    classroom = get_primary_classroom(request.user)
    if not classroom:
        raise PermissionDenied("担任権限がありません。")

    # 連絡帳を取得（クラスの生徒のもののみ）
    diary = get_object_or_404(
        DiaryEntry,
        id=diary_id,
        student__classes=classroom,
    )

    # 対応内容メモを取得
    action_note = request.POST.get("action_note", "").strip()

    # 対応完了処理
    DiaryEntryService.complete_action(diary, request.user, note=action_note)

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
    classroom = get_primary_classroom(request.user)
    if not classroom:
        raise PermissionDenied("担任権限がありません。")

    # 生徒を取得（自分のクラスの生徒のみ）
    student = get_object_or_404(User, id=student_id, classes=classroom)

    # メモ内容を取得
    note = request.POST.get("note", "").strip()
    is_shared_value = request.POST.get("is_shared", "")
    is_shared = is_shared_value in ["on", "True", "true", "1"]

    # バリデーション
    try:
        TeacherNoteService.create_note(
            teacher=request.user,
            student=student,
            note=note,
            is_shared=is_shared,
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("diary:teacher_student_detail", student_id=student_id)

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
        raise PermissionDenied("このメモを編集する権限がありません。")

    # メモ内容を取得
    note = request.POST.get("note", "").strip()
    is_shared_value = request.POST.get("is_shared", "")
    is_shared = is_shared_value in ["on", "True", "true", "1"]

    # バリデーション
    try:
        TeacherNoteService.update_teacher_note(
            teacher_note,
            note=note,
            is_shared=is_shared,
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("diary:teacher_student_detail", student_id=teacher_note.student.id)

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
        raise PermissionDenied("このメモを削除する権限がありません。")

    student_id = teacher_note.student.id
    student_name = teacher_note.student.get_full_name()

    TeacherNoteService.delete_note(teacher_note)

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

    TeacherNoteService.mark_shared_note_read(teacher=request.user, note=note)

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
    classroom = get_primary_classroom(request.user)
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
        DiaryEntryService.save_attendance(
            attendance_model=DailyAttendance,
            student=student,
            classroom=classroom,
            date=date,
            status=status,
            noted_by=request.user,
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
            DiaryEntryService.save_attendance(
                attendance_model=DailyAttendance,
                student=student,
                classroom=classroom,
                date=today,
                status=status,
                noted_by=request.user,
                absence_reason=absence_reason,
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
    classroom = get_primary_classroom(request.user)
    if not classroom:
        return JsonResponse({"status": "error", "message": "権限がありません"}, status=403)

    diary = get_object_or_404(DiaryEntry, id=diary_id, student__classes=classroom)
    DiaryEntryService.mark_as_read_quick(diary, request.user)

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
    classroom = get_primary_classroom(request.user)
    if not classroom:
        return JsonResponse({"status": "error", "message": "権限がありません"}, status=403)

    diary = get_object_or_404(DiaryEntry, id=diary_id, student__classes=classroom)

    # JSON dataからinternal_actionを取得
    try:
        data = json.loads(request.body)
        internal_action = data.get("internal_action")
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"status": "error", "message": "不正なリクエストです"}, status=400)

    if not internal_action:
        return JsonResponse({"status": "error", "message": "internal_actionが必要です"}, status=400)

    DiaryEntryService.create_action_task(diary, request.user, internal_action)

    return JsonResponse({"status": "success", "message": "タスク化しました"})

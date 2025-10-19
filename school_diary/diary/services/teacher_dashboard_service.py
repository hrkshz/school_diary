"""TeacherDashboardViewのビジネスロジック管理"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch, Q
from django.utils import timezone

from school_diary.diary.constants import NoteSettings
from school_diary.diary.models import (
    AbsenceReason,
    ActionStatus,
    AttendanceStatus,
    DailyAttendance,
    DiaryEntry,
    InternalAction,
    TeacherNote,
)

User = get_user_model()


class TeacherDashboardService:
    """担任ダッシュボード用のビジネスロジック"""

    @staticmethod
    def get_classroom_summary(classroom):
        """サマリー統計を一括計算

        Args:
            classroom: 対象クラス (ClassRoomインスタンス)

        Returns:
            dict: サマリー統計
                - unread_total: 未読連絡帳の総数
                - pending_action_count: 対応待ちの連絡帳数
                - urgent_action_count: 緊急対応が必要な連絡帳数
                - no_reaction_count: 既読だが反応なしの連絡帳数

        パフォーマンス:
            - 1つのクエリで全て集計（N+1問題回避）
        """
        return DiaryEntry.objects.filter(
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

    @staticmethod
    def get_student_list_with_unread_count(classroom):
        """生徒一覧を取得（未読件数をアノテーション）

        Args:
            classroom: 対象クラス (ClassRoomインスタンス)

        Returns:
            QuerySet: 生徒一覧（未読件数付き、名前順ソート）
                - unread_count: 各生徒の未読連絡帳数（アノテーション）
                - latest_entry_list: 最新の連絡帳1件（Prefetch、to_attr）

        パフォーマンス:
            - N+1問題回避（annotate + prefetch_related）
            - 生徒数35名で数ミリ秒
        """
        return (
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

    @staticmethod
    def get_absence_data(classroom, today):
        """本日の欠席者情報を集計

        Args:
            classroom: 対象クラス
            today: 対象日付

        Returns:
            dict: 欠席データ
                - total_absent: 欠席者総数
                - absent_illness: 病気欠席者数
                - absent_students: 欠席者リスト（詳細情報付き）
        """
        today_attendance = DailyAttendance.objects.filter(
            classroom=classroom,
            date=today,
        )

        absent_students = []
        for attendance in today_attendance.filter(
            status=AttendanceStatus.ABSENT
        ).select_related("student"):
            absent_students.append(
                {
                    "student": attendance.student,
                    "absence_reason": (
                        attendance.get_absence_reason_display()
                        if attendance.absence_reason
                        else "未設定"
                    ),
                    "absence_reason_code": attendance.absence_reason,
                }
            )

        return {
            "total_absent": len(absent_students),
            "absent_illness": today_attendance.filter(
                status=AttendanceStatus.ABSENT,
                absence_reason=AbsenceReason.ILLNESS,
            ).count(),
            "absent_students": absent_students,
        }

    @staticmethod
    def get_attendance_data_for_modal(classroom, today, student_data):
        """出席入力モーダル用のデータを準備

        Args:
            classroom: 対象クラス
            today: 対象日付
            student_data: 生徒データリスト（未読件数等を含む）

        Returns:
            tuple: (更新後のstudent_data, 全生徒リスト)
                - student_data: 出席情報が追加された生徒データリスト
                - all_students: 全生徒リスト（出席情報付き）

        Note:
            student_dataに出席情報を追加し、モーダル表示用の全生徒リストも生成
        """
        # 今日の出席データを取得
        today_attendance_records = DailyAttendance.objects.filter(
            classroom=classroom,
            date=today,
        ).select_related("student")

        # 生徒IDをキーとした辞書に変換
        attendance_by_student_id = {}
        for record in today_attendance_records:
            attendance_by_student_id[record.student_id] = {
                "status": record.status,
                "absence_reason": record.absence_reason,
            }

        # 出席情報をstudent_dataに追加（N+1問題回避済み）
        for data in student_data:
            attendance_data = attendance_by_student_id.get(data["student"].id)
            data["attendance_status"] = (
                attendance_data["status"] if attendance_data else "present"
            )
            data["absence_reason"] = (
                attendance_data["absence_reason"] if attendance_data else None
            )

        # 全生徒リストに出席データを付加
        all_students_with_attendance = []
        for student in classroom.students.all().order_by("last_name", "first_name"):
            attendance_data = attendance_by_student_id.get(student.id)
            student.attendance_status = (
                attendance_data["status"] if attendance_data else "present"
            )
            student.attendance_absence_reason = (
                attendance_data["absence_reason"] if attendance_data else None
            )
            all_students_with_attendance.append(student)

        return student_data, all_students_with_attendance

    @staticmethod
    def get_shared_notes(classroom, user):
        """学年共有メモを取得

        Args:
            classroom: 対象クラス
            user: リクエストユーザー（担任）

        Returns:
            QuerySet: 学年共有メモリスト（最新N件、未読のみ）

        Note:
            - 同じ学年の他クラス担任からの共有メモ
            - 過去N日以内
            - 自分が作成したもの、既読済みのものは除外
        """
        # 同じ学年・同じ年度のクラスIDリストを取得
        from school_diary.diary.models import ClassRoom

        same_grade_classrooms = ClassRoom.objects.filter(
            grade=classroom.grade,
            academic_year=classroom.academic_year,
        ).values_list("id", flat=True)

        # そのクラスの生徒IDリストを取得
        same_grade_students = User.objects.filter(
            classes__id__in=same_grade_classrooms,
        ).values_list("id", flat=True)

        # その生徒の共有メモを取得
        return (
            TeacherNote.objects.filter(
                student_id__in=same_grade_students,
                is_shared=True,
                created_at__gte=timezone.now()
                - timedelta(days=NoteSettings.SHARED_NOTE_DAYS),
            )
            .exclude(
                teacher=user,
            )
            .exclude(
                read_statuses__teacher=user,  # 既読済みメモを除外
            )
            .select_related("student", "teacher")
            .prefetch_related("student__classes")
            .order_by("-created_at")[: NoteSettings.SHARED_NOTE_LIMIT]
        )

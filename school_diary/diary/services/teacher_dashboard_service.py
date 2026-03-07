"""Teacher dashboard business logic."""

from collections import defaultdict
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models import Prefetch
from django.db.models import Q
from django.utils import timezone

from school_diary.diary.authorization import get_primary_classroom
from school_diary.diary.constants import HealthThresholds
from school_diary.diary.constants import NoteSettings
from school_diary.diary.models import AbsenceReason
from school_diary.diary.models import ActionStatus
from school_diary.diary.models import AttendanceStatus
from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DailyAttendance
from school_diary.diary.models import DiaryEntry
from school_diary.diary.models import InternalAction
from school_diary.diary.models import TeacherNote
from school_diary.diary.services import alert_service
from school_diary.diary.utils import get_previous_school_day

User = get_user_model()


class TeacherDashboardService:
    """Business logic for teacher-facing dashboards."""

    @staticmethod
    def empty_dashboard_data():
        """Return the empty dashboard payload for users without a homeroom."""
        classified_students = {
            "important": [],
            "needs_attention": [],
            "needs_action": [],
            "not_submitted": [],
            "unread": [],
            "completed": [],
        }
        return {
            "classroom": None,
            "students": [],
            "today": timezone.now().date(),
            "summary": {
                "unread_total": 0,
                "pending_action_count": 0,
                "urgent_action_count": 0,
            },
            "today_not_submitted_count": 0,
            "absence_data": {"total_absent": 0, "absent_illness": 0, "absent_students": []},
            "all_students": [],
            "alerts": [],
            "classified_students": classified_students,
            **classified_students,
            "needs_response_count": 0,
            "shared_notes": [],
        }

    @classmethod
    def get_dashboard_data(cls, user):
        """Build the complete dashboard context for a teacher."""
        classroom = get_primary_classroom(user)
        if not classroom:
            return cls.empty_dashboard_data()

        today = timezone.now().date()
        summary_stats = cls.get_classroom_summary(classroom)
        students = cls.get_student_list_with_unread_count(classroom)

        student_data = []
        for student in students:
            latest_entry = student.latest_entry_list[0] if student.latest_entry_list else None
            today_entry = latest_entry if latest_entry and latest_entry.entry_date == today else None
            student_data.append(
                {
                    "student": student,
                    "unread_count": student.unread_count,
                    "latest_entry": today_entry,
                },
            )

        student_data, all_students = cls.get_attendance_data_for_modal(classroom, today, student_data)

        classified_students = cls.build_classified_students(classroom)

        return {
            "classroom": classroom,
            "students": student_data,
            "today": today,
            "summary": summary_stats,
            "today_not_submitted_count": sum(1 for item in student_data if item["latest_entry"] is None),
            "absence_data": cls.get_absence_data(classroom, today),
            "all_students": all_students,
            "alerts": cls.build_alerts(classroom, today),
            "classified_students": classified_students,
            **classified_students,
            "needs_response_count": len(classified_students["not_submitted"]) + len(classified_students["unread"]),
            "shared_notes": cls.get_shared_notes(classroom, user),
        }

    @staticmethod
    def get_classroom_summary(classroom):
        """Aggregate top-level summary statistics."""
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
        )

    @staticmethod
    def get_student_list_with_unread_count(classroom):
        """Return students with unread counts and latest entry."""
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
                    queryset=DiaryEntry.objects.select_related("action_completed_by").order_by("-entry_date")[:1],
                    to_attr="latest_entry_list",
                ),
            )
            .order_by("last_name", "first_name")
        )

    @staticmethod
    def get_absence_data(classroom, today):
        """Collect absence data for the current day."""
        today_attendance = DailyAttendance.objects.filter(
            classroom=classroom,
            date=today,
        )

        absent_students = [
            {
                "student": attendance.student,
                "absence_reason": (
                    attendance.get_absence_reason_display() if attendance.absence_reason else "未設定"
                ),
                "absence_reason_code": attendance.absence_reason,
            }
            for attendance in today_attendance.filter(status=AttendanceStatus.ABSENT).select_related("student")
        ]

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
        """Attach attendance data to student rows and modal payload."""
        today_attendance_records = DailyAttendance.objects.filter(
            classroom=classroom,
            date=today,
        ).select_related("student")

        attendance_by_student_id = {
            record.student_id: {
                "status": record.status,
                "absence_reason": record.absence_reason,
            }
            for record in today_attendance_records
        }

        for data in student_data:
            attendance_data = attendance_by_student_id.get(data["student"].id)
            data["attendance_status"] = attendance_data["status"] if attendance_data else AttendanceStatus.PRESENT
            data["absence_reason"] = attendance_data["absence_reason"] if attendance_data else None

        all_students = []
        for student in classroom.students.all().order_by("last_name", "first_name"):
            attendance_data = attendance_by_student_id.get(student.id)
            student.attendance_status = attendance_data["status"] if attendance_data else AttendanceStatus.PRESENT
            student.attendance_absence_reason = attendance_data["absence_reason"] if attendance_data else None
            all_students.append(student)

        return student_data, all_students

    @classmethod
    def build_alerts(cls, classroom, today):
        """Build alert cards for the teacher dashboard."""
        alerts = []
        recent_entries = (
            DiaryEntry.objects.filter(
                student__classes=classroom,
                entry_date__gte=today - timedelta(days=7),
                entry_date__lt=today,
            )
            .select_related("student")
            .order_by("student_id", "-entry_date")
        )
        entries_by_student_id = defaultdict(list)
        for entry in recent_entries:
            entries_by_student_id[entry.student_id].append(entry)

        absent_dates = defaultdict(set)
        for record in DailyAttendance.objects.filter(
            classroom=classroom,
            status=AttendanceStatus.ABSENT,
            date__gte=today - timedelta(days=7),
            date__lt=today,
        ):
            absent_dates[record.student_id].add(record.date)

        for student in classroom.students.all():
            student_entries = [
                entry for entry in entries_by_student_id.get(student.id, []) if entry.entry_date not in absent_dates[student.id]
            ]
            latest_entry = student_entries[0] if student_entries else None
            if latest_entry and latest_entry.mental_condition == 1:
                alerts.append(
                    {
                        "level": "critical",
                        "type": "mental_critical",
                        "student": student,
                        "message": f"{student.get_full_name()}さん - メンタル★1",
                        "date": latest_entry.entry_date,
                        "action": "声をかけてください。",
                    },
                )

            if len(student_entries) >= HealthThresholds.CONSECUTIVE_DAYS:
                recent_three = list(reversed(student_entries[: HealthThresholds.CONSECUTIVE_DAYS]))
                values = [entry.mental_condition for entry in recent_three]
                dates = [entry.entry_date for entry in recent_three]
                if values[0] >= values[1] >= values[2] and values[2] < values[0]:
                    alerts.append(
                        {
                            "level": "warning",
                            "type": "mental_decline",
                            "student": student,
                            "message": f"{student.get_full_name()}さん - メンタル低下が続いています",
                            "trend": " → ".join(f"{'★' * value}" for value in values),
                            "dates": dates,
                            "action": "注意して見守ってください。",
                        },
                    )

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
        return alerts

    @classmethod
    def build_classified_students(cls, classroom):
        """Build classified dashboard cards with recent history attached."""
        classified_students = alert_service.classify_students(classroom)
        student_ids = set()
        tuple_tiers = ("completed", "needs_action")

        for tier, values in classified_students.items():
            if tier in tuple_tiers:
                student_ids.update(student.id for student, _extra in values)
            else:
                student_ids.update(student.id for student in values)

        students_by_id = {}
        if student_ids:
            students = classroom.students.filter(id__in=student_ids).prefetch_related(
                Prefetch(
                    "diary_entries",
                    queryset=DiaryEntry.objects.order_by("-entry_date")[:3],
                    to_attr="recent_entries_for_history",
                ),
            )
            students_by_id = {student.id: student for student in students}

        def decorate(student):
            target = students_by_id.get(student.id, student)
            recent_entries = getattr(target, "recent_entries_for_history", [])
            if recent_entries:
                target.inline_history = alert_service.format_inline_history(recent_entries)
                target.latest_snippet = alert_service.get_snippet(recent_entries[0])
                target.latest_entry_id = recent_entries[0].id
            else:
                target.inline_history = ""
                target.latest_snippet = "未提出"
                target.latest_entry_id = None
            return target

        for tier in ("important", "needs_attention", "not_submitted", "unread"):
            classified_students[tier] = [decorate(student) for student in classified_students[tier]]

        completed_students = []
        for student, entry_date in classified_students["completed"]:
            target = decorate(student)
            target.completed_date = entry_date
            completed_students.append(target)
        classified_students["completed"] = completed_students

        needs_action_students = []
        for student, entry in classified_students["needs_action"]:
            target = decorate(student)
            target.internal_action = entry.internal_action
            target.internal_action_label = entry.get_internal_action_display()
            target.action_status = entry.action_status
            target.entry_date = entry.entry_date
            target.action_entry_id = entry.id
            target.latest_entry_id = entry.id
            needs_action_students.append(target)
        classified_students["needs_action"] = needs_action_students

        return classified_students

    @staticmethod
    def get_shared_notes(classroom, user):
        """Return unread shared notes for the teacher's grade cohort."""
        same_grade_classrooms = ClassRoom.objects.filter(
            grade=classroom.grade,
            academic_year=classroom.academic_year,
        ).values_list("id", flat=True)
        same_grade_students = User.objects.filter(
            classes__id__in=same_grade_classrooms,
        ).values_list("id", flat=True)
        return (
            TeacherNote.objects.filter(
                student_id__in=same_grade_students,
                is_shared=True,
                created_at__gte=timezone.now() - timedelta(days=NoteSettings.SHARED_NOTE_DAYS),
            )
            .exclude(teacher=user)
            .exclude(read_statuses__teacher=user)
            .select_related("student", "teacher")
            .prefetch_related("student__classes")
            .order_by("-created_at")[: NoteSettings.SHARED_NOTE_LIMIT]
        )

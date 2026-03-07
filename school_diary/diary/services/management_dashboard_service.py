"""Management dashboard business logic."""

from collections import defaultdict
from datetime import timedelta

from django.db.models import Prefetch
from django.utils import timezone

from school_diary.diary.authorization import get_latest_academic_year
from school_diary.diary.constants import DashboardSettings
from school_diary.diary.constants import GradeLevel
from school_diary.diary.constants import HealthThresholds
from school_diary.diary.models import AbsenceReason
from school_diary.diary.models import AttendanceStatus
from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DailyAttendance
from school_diary.diary.models import DiaryEntry


class ManagementDashboardService:
    """Business logic for class, grade, and school dashboards."""

    @classmethod
    def get_class_health_dashboard_data(cls, *, classroom, days):
        """Build class health dashboard payload."""
        if not classroom:
            return {
                "classroom": None,
                "students_matrix": [],
                "date_list": [],
                "summary": {},
                "days": days,
                "absence_summary": {},
                "grade_summary": {},
                "alerts": [],
                "daily_summary": {},
            }

        today = timezone.now().date()
        end_date = today
        start_date = end_date - timedelta(days=days - 1)
        date_list = [start_date + timedelta(days=index) for index in range(days)]
        date_list.reverse()

        entries = DiaryEntry.objects.filter(
            student__classes=classroom,
            entry_date__gte=start_date,
            entry_date__lte=end_date,
        ).select_related("student")
        entries_by_student_id = defaultdict(list)
        for entry in entries:
            entries_by_student_id[entry.student_id].append(entry)

        students = list(classroom.students.all().order_by("last_name", "first_name"))
        daily_summary = {date: {"poor_health": 0, "poor_mental": 0} for date in date_list}
        poor_health_students = set()
        poor_mental_students = set()
        total_expected_entries = len(students) * days
        total_submitted_entries = 0
        students_matrix = []

        for student in students:
            row = {"student": student, "entries": {}}
            for entry in entries_by_student_id.get(student.id, []):
                row["entries"][entry.entry_date] = entry
                total_submitted_entries += 1
                if entry.health_condition <= HealthThresholds.POOR_CONDITION:
                    poor_health_students.add(student.id)
                    daily_summary[entry.entry_date]["poor_health"] += 1
                if entry.mental_condition <= HealthThresholds.POOR_CONDITION:
                    poor_mental_students.add(student.id)
                    daily_summary[entry.entry_date]["poor_mental"] += 1
            students_matrix.append(row)

        submission_rate = (
            round(total_submitted_entries / total_expected_entries * 100, 1) if total_expected_entries > 0 else 0
        )
        summary = {
            "submission_rate": submission_rate,
            "poor_health_count": len(poor_health_students),
            "poor_mental_count": len(poor_mental_students),
            "total_students": len(students),
            "days": days,
        }

        grade_summary = cls._build_grade_summary(classroom, start_date, end_date, today, summary)
        today_attendance = DailyAttendance.objects.filter(classroom=classroom, date=today)
        absence_summary = {
            "total_absent": today_attendance.filter(status=AttendanceStatus.ABSENT).count(),
            "absent_illness": today_attendance.filter(
                status=AttendanceStatus.ABSENT,
                absence_reason=AbsenceReason.ILLNESS,
            ).count(),
        }

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
            alerts.append(f"📝 提出率が{submission_rate}%です。未提出者への声かけをお願いします。")

        return {
            "classroom": classroom,
            "students_matrix": students_matrix,
            "date_list": date_list,
            "daily_summary": daily_summary,
            "summary": summary,
            "grade_summary": grade_summary,
            "absence_summary": absence_summary,
            "alerts": alerts,
            "days": days,
        }

    @staticmethod
    def _build_grade_summary(classroom, start_date, end_date, today, summary):
        """Build grade comparison block for class health dashboard."""
        grade_classrooms = (
            ClassRoom.objects.filter(
                grade=classroom.grade,
                academic_year=classroom.academic_year,
            )
            .exclude(id=classroom.id)
            .prefetch_related("students")
        )
        if not grade_classrooms.exists():
            return {
                "my_class_poor_health": summary["poor_health_count"],
                "my_class_poor_mental": summary["poor_mental_count"],
                "my_class_absent_today": DailyAttendance.objects.filter(
                    classroom=classroom,
                    date=today,
                    status=AttendanceStatus.ABSENT,
                ).count(),
                "single_class": True,
            }

        all_grade_students = []
        grade_total_students = 0
        for other_classroom in grade_classrooms:
            other_students = list(other_classroom.students.all())
            all_grade_students.extend(other_students)
            grade_total_students += len(other_students)

        grade_poor_health_students = set()
        grade_poor_mental_students = set()
        if all_grade_students:
            for entry in DiaryEntry.objects.filter(
                student__in=all_grade_students,
                entry_date__gte=start_date,
                entry_date__lte=end_date,
            ):
                if entry.health_condition <= HealthThresholds.POOR_CONDITION:
                    grade_poor_health_students.add(entry.student_id)
                if entry.mental_condition <= HealthThresholds.POOR_CONDITION:
                    grade_poor_mental_students.add(entry.student_id)

        denominator = grade_classrooms.count()
        grade_absent_today = DailyAttendance.objects.filter(
            classroom__in=grade_classrooms,
            date=today,
            status=AttendanceStatus.ABSENT,
        ).count()
        my_class_absent_today = DailyAttendance.objects.filter(
            classroom=classroom,
            date=today,
            status=AttendanceStatus.ABSENT,
        ).count()

        grade_avg_poor_health = round(len(grade_poor_health_students) / denominator, 1)
        grade_avg_poor_mental = round(len(grade_poor_mental_students) / denominator, 1)
        grade_avg_absent_today = round(grade_absent_today / denominator, 1)

        return {
            "total_students": grade_total_students + summary["total_students"],
            "class_count": denominator + 1,
            "avg_poor_health": grade_avg_poor_health,
            "avg_poor_mental": grade_avg_poor_mental,
            "avg_absent_today": grade_avg_absent_today,
            "my_class_poor_health": summary["poor_health_count"],
            "my_class_poor_mental": summary["poor_mental_count"],
            "my_class_absent_today": my_class_absent_today,
            "diff_poor_health": round(summary["poor_health_count"] - grade_avg_poor_health, 1),
            "diff_poor_mental": round(summary["poor_mental_count"] - grade_avg_poor_mental, 1),
            "diff_absent_today": round(my_class_absent_today - grade_avg_absent_today, 1),
        }

    @classmethod
    def get_grade_overview_data(cls, *, managed_grade):
        """Build grade overview payload for a grade leader."""
        current_year = get_latest_academic_year()
        classrooms = ClassRoom.objects.filter(
            grade=managed_grade,
            academic_year=current_year,
        ).prefetch_related("students")

        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        classroom_stats = []

        for classroom in classrooms:
            students = list(classroom.students.all())
            student_count = len(students)
            entries = DiaryEntry.objects.filter(
                student__in=students,
                entry_date__gte=week_ago,
                entry_date__lte=today,
            )
            today_attendance = DailyAttendance.objects.filter(classroom=classroom, date=today)
            absent_count = today_attendance.filter(status=AttendanceStatus.ABSENT).count()
            absent_illness = today_attendance.filter(
                status=AttendanceStatus.ABSENT,
                absence_reason=AbsenceReason.ILLNESS,
            ).count()
            attendance_rate = round(((student_count - absent_count) / student_count * 100), 1) if student_count > 0 else 0
            poor_health_count = (
                entries.filter(health_condition__lte=HealthThresholds.POOR_CONDITION).values("student").distinct().count()
            )
            poor_mental_count = (
                entries.filter(mental_condition__lte=HealthThresholds.POOR_CONDITION).values("student").distinct().count()
            )

            alert_level = "success"
            if (
                absent_illness >= HealthThresholds.CLASS_ALERT_THRESHOLD
                or poor_health_count >= HealthThresholds.CLASS_ALERT_THRESHOLD
            ):
                alert_level = "danger"
            elif absent_illness >= HealthThresholds.CONSECUTIVE_DAYS or poor_health_count >= HealthThresholds.CONSECUTIVE_DAYS:
                alert_level = "warning"

            classroom_stats.append(
                {
                    "classroom": classroom,
                    "student_count": student_count,
                    "attendance_rate": attendance_rate,
                    "absent_count": absent_count,
                    "absent_illness": absent_illness,
                    "poor_health_count": poor_health_count,
                    "poor_mental_count": poor_mental_count,
                    "alert_level": alert_level,
                },
            )

        escalation_alerts = []
        for classroom in classrooms:
            students_with_entries = classroom.students.prefetch_related(
                Prefetch(
                    "diary_entries",
                    queryset=DiaryEntry.objects.order_by("-entry_date")[:3],
                    to_attr="recent_entries_for_escalation",
                ),
            )
            for student in students_with_entries:
                recent_entries = student.recent_entries_for_escalation
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

        summary = {
            "total_students": sum(item["student_count"] for item in classroom_stats),
            "class_count": len(classroom_stats),
            "avg_attendance_rate": (
                round(sum(item["attendance_rate"] for item in classroom_stats) / len(classroom_stats), 1)
                if classroom_stats
                else 0
            ),
            "total_absent": sum(item["absent_count"] for item in classroom_stats),
            "total_absent_illness": sum(item["absent_illness"] for item in classroom_stats),
            "total_poor_health": sum(item["poor_health_count"] for item in classroom_stats),
            "total_poor_mental": sum(item["poor_mental_count"] for item in classroom_stats),
        }
        return {
            "managed_grade": managed_grade,
            "classroom_stats": classroom_stats,
            "summary": summary,
            "escalation_alerts": escalation_alerts,
        }

    @classmethod
    def get_school_overview_data(cls):
        """Build school overview payload."""
        current_year = get_latest_academic_year()
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        grade_stats = []

        for grade in [GradeLevel.GRADE_1, GradeLevel.GRADE_2, GradeLevel.GRADE_3]:
            classrooms = ClassRoom.objects.filter(
                grade=grade,
                academic_year=current_year,
            ).prefetch_related("students")
            all_students = []
            for classroom in classrooms:
                all_students.extend(list(classroom.students.all()))
            student_count = len(all_students)
            entries = DiaryEntry.objects.filter(
                student__in=all_students,
                entry_date__gte=week_ago,
                entry_date__lte=today,
            )
            today_attendance = DailyAttendance.objects.filter(classroom__in=classrooms, date=today)
            absent_count = today_attendance.filter(status=AttendanceStatus.ABSENT).count()
            absent_illness = today_attendance.filter(
                status=AttendanceStatus.ABSENT,
                absence_reason=AbsenceReason.ILLNESS,
            ).count()
            absence_rate = round((absent_count / student_count * 100), 1) if student_count > 0 else 0
            attendance_rate = round(((student_count - absent_count) / student_count * 100), 1) if student_count > 0 else 0
            poor_health_count = (
                entries.filter(health_condition__lte=HealthThresholds.POOR_CONDITION).values("student").distinct().count()
            )
            poor_mental_count = (
                entries.filter(mental_condition__lte=HealthThresholds.POOR_CONDITION).values("student").distinct().count()
            )

            alert_level = "success"
            if absence_rate >= 15:
                alert_level = "danger"
            elif absence_rate >= 10:
                alert_level = "warning"

            grade_stats.append(
                {
                    "grade": grade,
                    "grade_display": f"{grade}年",
                    "class_count": classrooms.count(),
                    "student_count": student_count,
                    "attendance_rate": attendance_rate,
                    "absent_count": absent_count,
                    "absent_illness": absent_illness,
                    "absence_rate": absence_rate,
                    "poor_health_count": poor_health_count,
                    "poor_mental_count": poor_mental_count,
                    "alert_level": alert_level,
                },
            )

        school_alert_level = "success"
        if any(item["alert_level"] == "danger" for item in grade_stats):
            school_alert_level = "danger"
        elif any(item["alert_level"] == "warning" for item in grade_stats):
            school_alert_level = "warning"

        return {
            "grade_stats": grade_stats,
            "summary": {
                "total_students": sum(item["student_count"] for item in grade_stats),
                "avg_attendance_rate": round(sum(item["attendance_rate"] for item in grade_stats) / 3, 1)
                if grade_stats
                else 0,
                "total_absent": sum(item["absent_count"] for item in grade_stats),
                "total_absent_illness": sum(item["absent_illness"] for item in grade_stats),
                "total_poor_health": sum(item["poor_health_count"] for item in grade_stats),
                "total_poor_mental": sum(item["poor_mental_count"] for item in grade_stats),
                "school_alert_level": school_alert_level,
            },
        }

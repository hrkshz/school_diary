"""Management views - class health, grade overview, school overview."""

from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView

from ..constants import DashboardSettings
from ..constants import GradeLevel
from ..constants import HealthThresholds
from ..models import AbsenceReason
from ..models import AttendanceStatus
from ..models import ClassRoom
from ..models import DailyAttendance
from ..models import DiaryEntry

__all__ = [
    "ClassHealthDashboardView",
    "GradeOverviewView",
    "SchoolOverviewView",
]


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

        # 本日の欠席者情報を集計
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
            # 本日の出席率 = (学生数 - 欠席者数) / 学生数 × 100
            attendance_rate = round(((student_count - absent_count) / student_count * 100), 1) if student_count > 0 else 0

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
                    "attendance_rate": attendance_rate,
                    "absent_count": absent_count,
                    "absent_illness": absent_illness,
                    "poor_health_count": poor_health_count,
                    "poor_mental_count": poor_mental_count,
                    "alert_level": alert_level,
                },
            )

        # 学年全体サマリー
        total_students = sum(s["student_count"] for s in classroom_stats)
        avg_attendance_rate = (
            round(sum(s["attendance_rate"] for s in classroom_stats) / len(classroom_stats), 1)
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
            "avg_attendance_rate": avg_attendance_rate,
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
            # 本日の出席率 = (学生数 - 欠席者数) / 学生数 × 100
            attendance_rate = round(((student_count - absent_count) / student_count * 100), 1) if student_count > 0 else 0

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
                    "attendance_rate": attendance_rate,
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
        avg_attendance_rate = round(sum(s["attendance_rate"] for s in grade_stats) / 3, 1) if grade_stats else 0

        # 全体の警告レベル
        school_alert_level = "success"
        if any(s["alert_level"] == "danger" for s in grade_stats):
            school_alert_level = "danger"
        elif any(s["alert_level"] == "warning" for s in grade_stats):
            school_alert_level = "warning"

        context["grade_stats"] = grade_stats
        context["summary"] = {
            "total_students": total_students,
            "avg_attendance_rate": avg_attendance_rate,
            "total_absent": total_absent,
            "total_absent_illness": total_absent_illness,
            "total_poor_health": total_poor_health,
            "total_poor_mental": total_poor_mental,
            "school_alert_level": school_alert_level,
        }

        return context

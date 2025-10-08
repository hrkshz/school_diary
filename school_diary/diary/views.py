"""Views for diary app."""

from django.views.generic import TemplateView


class StudentDashboardView(TemplateView):
    """生徒用ダッシュボード

    生徒がログイン後に表示されるメインページ。
    """

    template_name = "diary/student_dashboard.html"


class TeacherDashboardView(TemplateView):
    """担任用ダッシュボード

    担任がログイン後に表示されるメインページ。
    """

    template_name = "diary/teacher_dashboard.html"

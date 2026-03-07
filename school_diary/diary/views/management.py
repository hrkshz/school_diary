"""Management views - class health, grade overview, school overview."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

from ..authorization import get_primary_classroom
from ..authorization import get_user_role
from ..constants import DashboardSettings
from ..models import UserProfile
from ..services.management_dashboard_service import ManagementDashboardService

__all__ = [
    "ClassHealthDashboardView",
    "GradeOverviewView",
    "SchoolOverviewView",
]


class ClassHealthDashboardView(LoginRequiredMixin, TemplateView):
    """クラス健康状態ダッシュボード"""

    template_name = "diary/class_health_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        days = int(self.request.GET.get("days", DashboardSettings.HEALTH_DASHBOARD_DEFAULT_DAYS))
        if days not in DashboardSettings.HEALTH_DASHBOARD_DAYS:
            days = DashboardSettings.HEALTH_DASHBOARD_DEFAULT_DAYS
        context.update(
            ManagementDashboardService.get_class_health_dashboard_data(
                classroom=get_primary_classroom(self.request.user),
                days=days,
            ),
        )
        return context


class GradeOverviewView(LoginRequiredMixin, TemplateView):
    """学年主任用ダッシュボード（学年全体の比較）"""

    template_name = "diary/grade_overview.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and get_user_role(request.user) != UserProfile.ROLE_GRADE_LEADER:
            raise PermissionDenied("学年主任権限が必要です。")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            ManagementDashboardService.get_grade_overview_data(
                managed_grade=self.request.user.profile.managed_grade,
            ),
        )
        return context


class SchoolOverviewView(LoginRequiredMixin, TemplateView):
    """校長/教頭用ダッシュボード（学校全体の把握）"""

    template_name = "diary/school_overview.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser and get_user_role(request.user) != UserProfile.ROLE_SCHOOL_LEADER:
            raise PermissionDenied("校長/教頭権限が必要です。")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(ManagementDashboardService.get_school_overview_data())
        return context

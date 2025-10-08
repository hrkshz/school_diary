"""URL configuration for diary app."""

from django.urls import path

from . import views

app_name = "diary"

urlpatterns = [
    path(
        "student/dashboard/",
        views.StudentDashboardView.as_view(),
        name="student_dashboard",
    ),
    path(
        "teacher/dashboard/",
        views.TeacherDashboardView.as_view(),
        name="teacher_dashboard",
    ),
    # 以下はダミー実装（MLP-6, MLP-7で本実装予定）
    path(
        "diary/create/",
        views.DiaryCreateView.as_view(),
        name="diary_create",
    ),
    path(
        "diary/history/",
        views.DiaryHistoryView.as_view(),
        name="diary_history",
    ),
]

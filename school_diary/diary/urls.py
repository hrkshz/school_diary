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
]

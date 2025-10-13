"""URL configuration for diary app."""

from django.urls import path

from . import views

app_name = "diary"

urlpatterns = [
    # 生徒用
    path(
        "student/dashboard/",
        views.StudentDashboardView.as_view(),
        name="student_dashboard",
    ),
    path(
        "create/",
        views.DiaryCreateView.as_view(),
        name="diary_create",
    ),
    path(
        "history/",
        views.DiaryHistoryView.as_view(),
        name="diary_history",
    ),
    # 担任用
    path(
        "teacher/dashboard/",
        views.TeacherDashboardView.as_view(),
        name="teacher_dashboard",
    ),
    path(
        "teacher/class-health/",
        views.ClassHealthDashboardView.as_view(),
        name="class_health_dashboard",
    ),
    path(
        "teacher/student/<int:student_id>/",
        views.TeacherStudentDetailView.as_view(),
        name="teacher_student_detail",
    ),
    path(
        "teacher/diary/<int:diary_id>/mark-as-read/",
        views.teacher_mark_as_read,
        name="teacher_mark_as_read",
    ),
    path(
        "teacher/diary/<int:diary_id>/mark-action-completed/",
        views.teacher_mark_action_completed,
        name="teacher_mark_action_completed",
    ),
    # 担任メモ管理
    path(
        "teacher/note/add/<int:student_id>/",
        views.teacher_add_note,
        name="teacher_add_note",
    ),
    path(
        "teacher/note/edit/<int:note_id>/",
        views.teacher_edit_note,
        name="teacher_edit_note",
    ),
    path(
        "teacher/note/delete/<int:note_id>/",
        views.teacher_delete_note,
        name="teacher_delete_note",
    ),
    # 出席管理
    path(
        "teacher/attendance/save/",
        views.teacher_save_attendance,
        name="teacher_save_attendance",
    ),
    # 管理職画面
    path(
        "grade-overview/",
        views.GradeOverviewView.as_view(),
        name="grade_overview",
    ),
    path(
        "school-overview/",
        views.SchoolOverviewView.as_view(),
        name="school_overview",
    ),
]

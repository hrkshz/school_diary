"""URL configuration for diary app."""

from django.urls import path

from .views.admin_views import test_data_complete
from .views.admin_views import test_data_config
from .views.admin_views import test_data_confirm
from .views.admin_views import test_data_loading
from .views.auth import health_check
from .views.management import ClassHealthDashboardView
from .views.management import GradeOverviewView
from .views.management import SchoolOverviewView
from .views.student import DiaryCreateView
from .views.student import DiaryHistoryView
from .views.student import DiaryUpdateView
from .views.student import StudentDashboardView
from .views.teacher import TeacherDashboardView
from .views.teacher import TeacherStudentDetailView
from .views.teacher import mark_shared_note_read
from .views.teacher import teacher_add_note
from .views.teacher import teacher_create_task_from_card
from .views.teacher import teacher_delete_note
from .views.teacher import teacher_edit_note
from .views.teacher import teacher_mark_action_completed
from .views.teacher import teacher_mark_as_read
from .views.teacher import teacher_mark_as_read_quick
from .views.teacher import teacher_save_attendance

app_name = "diary"

urlpatterns = [
    # Health Check (ALB用、認証不要)
    path("health/", health_check, name="health_check"),
    # 管理者用 - テストデータ作成
    path(
        "admin/test-data/config/",
        test_data_config,
        name="test_data_config",
    ),
    path(
        "admin/test-data/confirm/",
        test_data_confirm,
        name="test_data_confirm",
    ),
    path(
        "admin/test-data/loading/",
        test_data_loading,
        name="test_data_loading",
    ),
    path(
        "admin/test-data/complete/",
        test_data_complete,
        name="test_data_complete",
    ),
    # 生徒用
    path(
        "student/dashboard/",
        StudentDashboardView.as_view(),
        name="student_dashboard",
    ),
    path(
        "create/",
        DiaryCreateView.as_view(),
        name="diary_create",
    ),
    path(
        "diary/<int:pk>/edit/",
        DiaryUpdateView.as_view(),
        name="diary_update",
    ),
    path(
        "history/",
        DiaryHistoryView.as_view(),
        name="diary_history",
    ),
    # 担任用
    path(
        "teacher/dashboard/",
        TeacherDashboardView.as_view(),
        name="teacher_dashboard",
    ),
    path(
        "teacher/class-health/",
        ClassHealthDashboardView.as_view(),
        name="class_health_dashboard",
    ),
    path(
        "teacher/student/<int:student_id>/",
        TeacherStudentDetailView.as_view(),
        name="teacher_student_detail",
    ),
    path(
        "teacher/diary/<int:diary_id>/mark-as-read/",
        teacher_mark_as_read,
        name="teacher_mark_as_read",
    ),
    # カードから既読のみ（AJAX用）
    path(
        "teacher/diary/<int:diary_id>/mark-as-read-quick/",
        teacher_mark_as_read_quick,
        name="teacher_mark_as_read_quick",
    ),
    # カードからタスク化（AJAX用）
    path(
        "teacher/diary/<int:diary_id>/create-task/",
        teacher_create_task_from_card,
        name="teacher_create_task_from_card",
    ),
    path(
        "teacher/diary/<int:diary_id>/mark-action-completed/",
        teacher_mark_action_completed,
        name="teacher_mark_action_completed",
    ),
    # 担任メモ管理
    path(
        "teacher/note/add/<int:student_id>/",
        teacher_add_note,
        name="teacher_add_note",
    ),
    path(
        "teacher/note/edit/<int:note_id>/",
        teacher_edit_note,
        name="teacher_edit_note",
    ),
    path(
        "teacher/note/delete/<int:note_id>/",
        teacher_delete_note,
        name="teacher_delete_note",
    ),
    path(
        "teacher/note/<int:note_id>/mark-read/",
        mark_shared_note_read,
        name="mark_shared_note_read",
    ),
    # 出席管理
    path(
        "teacher/attendance/save/",
        teacher_save_attendance,
        name="teacher_save_attendance",
    ),
    # 管理職画面
    path(
        "grade-overview/",
        GradeOverviewView.as_view(),
        name="grade_overview",
    ),
    path(
        "school-overview/",
        SchoolOverviewView.as_view(),
        name="school_overview",
    ),
]

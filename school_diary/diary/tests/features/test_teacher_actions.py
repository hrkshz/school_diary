"""
03-features.md Teacher Actions Tests

このモジュールは以下の機能をテストします:
- TEA-ACT-001: 既読処理
- TEA-ACT-002: 対応完了処理
- TEA-ACT-003: メモ追加
- TEA-ACT-004: メモ編集
- TEA-ACT-005: メモ削除
- TEA-ACT-006: 共有メモ既読
- TEA-ACT-007: 出席保存
- TEA-ACT-008: 既読処理Quick（AJAX）
- TEA-ACT-009: タスク化（AJAX）

Traceability Matrix:
| Test Method | Feature ID | Scenario | Priority |
|-------------|------------|----------|----------|
| test_teaact001_mark_as_read_success | TEA-ACT-001 | 既読処理 | P0 |
| test_teaact001_mark_as_read_other_class_forbidden | TEA-ACT-001 | 他クラス禁止 | P0 |
| test_teaact002_mark_action_completed_success | TEA-ACT-002 | 対応完了 | P1 |
| test_teaact003_add_note_success | TEA-ACT-003 | メモ追加 | P1 |
| test_teaact003_add_shared_note_success | TEA-ACT-003 | 共有メモ追加 | P1 |
| test_teaact004_edit_note_success | TEA-ACT-004 | メモ編集 | P1 |
| test_teaact004_edit_note_other_teacher_forbidden | TEA-ACT-004 | 他担任禁止 | P1 |
| test_teaact005_delete_note_success | TEA-ACT-005 | メモ削除 | P1 |
| test_teaact005_delete_note_other_teacher_forbidden | TEA-ACT-005 | 他担任禁止 | P1 |
| test_teaact006_mark_shared_note_read_success | TEA-ACT-006 | 共有メモ既読 | P1 |
| test_teaact007_save_attendance_success | TEA-ACT-007 | 出席保存 | P1 |
| test_teaact008_mark_as_read_quick_ajax_success | TEA-ACT-008 | 既読Quick | P1 |
| test_teaact009_create_task_ajax_success | TEA-ACT-009 | タスク化 | P1 |
"""

import json

import pytest
from django.urls import reverse

from school_diary.diary.models import ActionStatus


@pytest.mark.django_db
class TestTEAACT001MarkAsRead:
    """TEA-ACT-001: 既読処理のテスト"""

    def test_teaact001_mark_as_read_success(
        self,
        authenticated_teacher_client,
        teacher_user,
        unread_diary_entry,
    ):
        """
        Given: 未読の連絡帳エントリー
        When: 既読処理を実行
        Then: is_read=True、反応・対応記録が更新される
        """
        # Arrange
        assert not unread_diary_entry.is_read

        data = {
            "public_reaction": "確認しました",
            "internal_action": "保護者に連絡します",
        }

        # Act
        response = authenticated_teacher_client.post(
            reverse("diary:teacher_mark_as_read", kwargs={"diary_id": unread_diary_entry.id}),
            data,
        )

        # Assert
        assert response.status_code == 302  # リダイレクト
        unread_diary_entry.refresh_from_db()
        assert unread_diary_entry.is_read
        assert unread_diary_entry.public_reaction == "確認しました"
        assert unread_diary_entry.internal_action == "保護者に連絡します"

    def test_teaact001_mark_as_read_other_class_forbidden(self, authenticated_teacher_client, teacher_user):
        """
        Given: 他のクラスの連絡帳エントリー
        When: 既読処理を試行
        Then: 403 Forbidden
        """
        # Arrange: 他のクラスの生徒と連絡帳作成
        from django.contrib.auth import get_user_model

        from school_diary.diary.models import ClassRoom
        from school_diary.diary.models import DiaryEntry

        User = get_user_model()
        other_classroom = ClassRoom.objects.create(
            class_name="B",
            grade=2,
            academic_year=2025,
        )
        other_student = User.objects.create_user(
            username="other_student@test.com",
            email="other_student@test.com",
            password="testpass123",
        )
        other_student.profile.role = "student"
        other_student.profile.save()
        other_classroom.students.add(other_student)

        other_entry = DiaryEntry.objects.create(
            student=other_student,
            entry_date="2025-10-24",
            health_condition=4,
            mental_condition=4,
            reflection="他クラスの連絡帳",
        )

        # Act
        response = authenticated_teacher_client.post(
            reverse("diary:teacher_mark_as_read", kwargs={"diary_id": other_entry.id}),
            {"teacher_reaction": "不正アクセス"},
        )

        # Assert
        assert response.status_code == 403


@pytest.mark.django_db
class TestTEAACT008MarkAsReadQuick:
    """TEA-ACT-008: 既読処理Quick（AJAX）のテスト"""

    def test_teaact008_mark_as_read_quick_ajax_success(
        self,
        authenticated_teacher_client,
        teacher_user,
        unread_diary_entry,
    ):
        """
        Given: 未読の連絡帳エントリー
        When: 既読Quick処理（AJAX）を実行
        Then: is_read=True、action_status=NOT_REQUIRED
        """
        # Arrange
        assert not unread_diary_entry.is_read

        # Act
        response = authenticated_teacher_client.post(
            reverse("diary:teacher_mark_as_read_quick", kwargs={"diary_id": unread_diary_entry.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["status"] == "success"

        unread_diary_entry.refresh_from_db()
        assert unread_diary_entry.is_read
        assert unread_diary_entry.action_status == ActionStatus.NOT_REQUIRED


@pytest.mark.django_db
class TestTEAACT009CreateTask:
    """TEA-ACT-009: タスク化（AJAX）のテスト"""

    def test_teaact009_create_task_ajax_success(
        self,
        authenticated_teacher_client,
        teacher_user,
        unread_diary_entry,
    ):
        """
        Given: 未読の連絡帳エントリー
        When: タスク化（AJAX）を実行
        Then: is_read=True、internal_action設定、action_status=IN_PROGRESS
        """
        # Arrange
        assert not unread_diary_entry.is_read

        data = {"internal_action": "parent_contact"}

        # Act
        response = authenticated_teacher_client.post(
            reverse("diary:teacher_create_task_from_card", kwargs={"diary_id": unread_diary_entry.id}),
            data=json.dumps(data),
            content_type="application/json",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # Assert
        assert response.status_code == 200
        response_data = json.loads(response.content)
        assert response_data["status"] == "success"

        unread_diary_entry.refresh_from_db()
        assert unread_diary_entry.is_read
        assert unread_diary_entry.internal_action == "parent_contact"
        assert unread_diary_entry.action_status == ActionStatus.IN_PROGRESS


@pytest.mark.django_db
class TestTEAACT002MarkActionCompleted:
    """TEA-ACT-002: 対応完了処理のテスト"""

    def test_teaact002_mark_action_completed_success(
        self,
        authenticated_teacher_client,
        teacher_user,
        unread_diary_entry,
    ):
        """
        Given: internal_action設定済みのエントリー
        When: 対応完了処理を実行
        Then: action_status=COMPLETED
        """
        # Arrange
        unread_diary_entry.internal_action = "parent_contact"
        unread_diary_entry.action_status = ActionStatus.IN_PROGRESS
        unread_diary_entry.save()

        # Act
        response = authenticated_teacher_client.post(
            reverse("diary:teacher_mark_action_completed", kwargs={"diary_id": unread_diary_entry.id}),
        )

        # Assert
        assert response.status_code == 302  # リダイレクト
        unread_diary_entry.refresh_from_db()
        assert unread_diary_entry.action_status == ActionStatus.COMPLETED
        assert unread_diary_entry.action_completed_by == teacher_user
        assert unread_diary_entry.action_completed_at is not None


@pytest.mark.django_db
class TestTEAACT003To005TeacherNotes:
    """TEA-ACT-003〜005: 担任メモのテスト"""

    def test_teaact003_add_note_success(
        self,
        authenticated_teacher_client,
        student_user,
    ):
        """
        Given: 担任ユーザー
        When: 個人メモを追加
        Then: TeacherNote作成成功、is_shared=False
        """
        # Arrange
        from school_diary.diary.models import TeacherNote

        data = {
            "note": "テストメモ：家庭環境良好",
            "is_shared": False,
        }

        # Act
        response = authenticated_teacher_client.post(
            reverse("diary:teacher_add_note", kwargs={"student_id": student_user.id}),
            data,
        )

        # Assert
        assert response.status_code == 302  # リダイレクト
        note = TeacherNote.objects.filter(student=student_user).first()
        assert note is not None
        assert note.note == "テストメモ：家庭環境良好"
        assert not note.is_shared

    def test_teaact003_add_shared_note_success(
        self,
        authenticated_teacher_client,
        student_user,
    ):
        """
        Given: 担任ユーザー
        When: 学年共有メモを追加
        Then: TeacherNote作成成功、is_shared=True
        """
        # Arrange
        from school_diary.diary.models import TeacherNote

        data = {
            "note": "学年共有メモ：要配慮事項あり",
            "is_shared": True,
        }

        # Act
        response = authenticated_teacher_client.post(
            reverse("diary:teacher_add_note", kwargs={"student_id": student_user.id}),
            data,
        )

        # Assert
        assert response.status_code == 302  # リダイレクト
        note = TeacherNote.objects.filter(student=student_user, is_shared=True).first()
        assert note is not None
        assert note.note == "学年共有メモ：要配慮事項あり"
        assert note.is_shared

    def test_teaact004_edit_note_success(
        self,
        authenticated_teacher_client,
        teacher_note,
    ):
        """
        Given: 自分が作成したメモ
        When: メモを編集
        Then: 編集成功
        """
        # Arrange
        data = {
            "note": "更新後のメモ内容（詳細追記）",
            "is_shared": False,
        }

        # Act
        response = authenticated_teacher_client.post(
            reverse("diary:teacher_edit_note", kwargs={"note_id": teacher_note.id}),
            data,
        )

        # Assert
        assert response.status_code == 302  # リダイレクト
        teacher_note.refresh_from_db()
        assert teacher_note.note == "更新後のメモ内容（詳細追記）"

    def test_teaact004_edit_note_other_teacher_forbidden(
        self,
        client,
        teacher_note,
        classroom,
    ):
        """
        Given: 他の担任が作成したメモ
        When: メモ編集を試行
        Then: 403 Forbidden
        """
        # Arrange: 別の担任を作成してログイン
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_teacher = User.objects.create_user(
            username="other_teacher@test.com",
            email="other_teacher@test.com",
            password="testpass123",
        )
        other_teacher.profile.role = "teacher"
        other_teacher.profile.save()
        client.force_login(other_teacher)

        data = {
            "note": "不正な編集",
            "is_shared": False,
        }

        # Act
        response = client.post(
            reverse("diary:teacher_edit_note", kwargs={"note_id": teacher_note.id}),
            data,
        )

        # Assert
        assert response.status_code == 403

    def test_teaact005_delete_note_success(
        self,
        authenticated_teacher_client,
        teacher_note,
    ):
        """
        Given: 自分が作成したメモ
        When: メモを削除
        Then: 削除成功
        """
        # Arrange
        note_id = teacher_note.id

        # Act
        response = authenticated_teacher_client.post(
            reverse("diary:teacher_delete_note", kwargs={"note_id": teacher_note.id}),
        )

        # Assert
        assert response.status_code == 302  # リダイレクト
        from school_diary.diary.models import TeacherNote

        assert not TeacherNote.objects.filter(id=note_id).exists()

    def test_teaact005_delete_note_other_teacher_forbidden(
        self,
        client,
        teacher_note,
        classroom,
    ):
        """
        Given: 他の担任が作成したメモ
        When: メモ削除を試行
        Then: 403 Forbidden
        """
        # Arrange: 別の担任を作成してログイン
        from django.contrib.auth import get_user_model

        User = get_user_model()
        other_teacher = User.objects.create_user(
            username="other_teacher2@test.com",
            email="other_teacher2@test.com",
            password="testpass123",
        )
        other_teacher.profile.role = "teacher"
        other_teacher.profile.save()
        client.force_login(other_teacher)

        # Act
        response = client.post(
            reverse("diary:teacher_delete_note", kwargs={"note_id": teacher_note.id}),
        )

        # Assert
        assert response.status_code == 403


@pytest.mark.django_db
class TestTEAACT006MarkSharedNoteRead:
    """TEA-ACT-006: 共有メモ既読のテスト"""

    def test_teaact006_mark_shared_note_read_success(
        self,
        client,
        shared_teacher_note,
        classroom,
    ):
        """
        Given: 学年の別の担任ユーザー
        When: 共有メモを既読にする
        Then: TeacherNoteReadStatus作成成功
        """
        # Arrange: 学年の別の担任を作成してログイン
        from django.contrib.auth import get_user_model

        from school_diary.diary.models import TeacherNoteReadStatus

        User = get_user_model()
        other_teacher = User.objects.create_user(
            username="grade_teacher@test.com",
            email="grade_teacher@test.com",
            password="testpass123",
        )
        other_teacher.profile.role = "teacher"
        other_teacher.profile.managed_grade = 1  # 同じ学年
        other_teacher.profile.save()
        client.force_login(other_teacher)

        # Act
        response = client.post(
            reverse("diary:mark_shared_note_read", kwargs={"note_id": shared_teacher_note.id}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["status"] == "success"

        # 既読ステータスが作成されていることを確認
        read_status = TeacherNoteReadStatus.objects.filter(
            teacher=other_teacher,
            note=shared_teacher_note,
        ).first()
        assert read_status is not None


@pytest.mark.django_db
class TestTEAACT007AttendanceSave:
    """TEA-ACT-007: 出席保存のテスト"""

    def test_teaact007_save_attendance_success(
        self,
        authenticated_teacher_client,
        student_user,
        today,
    ):
        """
        Given: 担任ユーザー
        When: 出席記録を保存
        Then: DailyAttendance作成成功
        """
        # Arrange
        from school_diary.diary.models import DailyAttendance

        data = {
            "student_id": student_user.id,
            "date": today.strftime("%Y-%m-%d"),
            "status": "present",
        }

        # Act
        response = authenticated_teacher_client.post(
            reverse("diary:teacher_save_attendance"),
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        # Assert
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["status"] == "success"

        # DailyAttendanceが作成されていることを確認
        attendance = DailyAttendance.objects.filter(
            student=student_user,
            date=today,
        ).first()
        assert attendance is not None
        assert attendance.status == "present"

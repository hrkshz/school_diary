"""N+1クエリ問題のテスト

H-MODEL-002: N+1クエリ解消（__str__メソッド）

このテストはDjangoのCaptureQueriesContextを使用して、
モデルの__str__()メソッドがN+1クエリを引き起こさないことを検証します。
"""

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from school_diary.diary.models import (
    ClassRoom,
    DailyAttendance,
    DiaryEntry,
    TeacherNote,
    TeacherNoteReadStatus,
)

User = get_user_model()


class TestDiaryEntryN1Queries(TestCase):
    """DiaryEntry.__str__()のN+1クエリテスト"""

    def setUp(self):
        """テストデータ準備"""
        # 教員ユーザー作成
        self.teacher = User.objects.create_user(
            username="teacher001", email="teacher001@example.com"
        )

        # 生徒ユーザー作成（10人）
        self.students = []
        for i in range(10):
            student = User.objects.create_user(
                username=f"student{i:03d}",
                email=f"student{i:03d}@example.com",
                first_name=f"太郎{i}",
                last_name=f"山田{i}",
            )
            self.students.append(student)

        # クラス作成
        self.classroom = ClassRoom.objects.create(
            grade=1, class_name="A", academic_year=2025, homeroom_teacher=self.teacher
        )
        self.classroom.students.set(self.students)

        # 連絡帳エントリー作成（10件）
        self.entries = []
        for i, student in enumerate(self.students):
            entry = DiaryEntry.objects.create(
                student=student,
                classroom=self.classroom,
                entry_date="2025-10-19",
                health_condition=3,
                mental_condition=3,
                reflection=f"今日の振り返り{i}",
            )
            self.entries.append(entry)

    def test_diary_entry_str_without_n1_queries(self):
        """DiaryEntry.__str__()がN+1クエリを起こさないことを確認"""
        # Arrange: with_related()を使用してprefetch
        entries = DiaryEntry.objects.with_related()[:10]

        # Act & Assert
        with CaptureQueriesContext(connection) as context:
            for entry in entries:
                _ = str(entry)  # __str__()呼び出し

        # N+1が起きている場合、クエリ数は10件以上になる
        # prefetch後は1-2クエリに削減されるべき
        # 現在はN+1が起きているので、このテストは失敗する
        num_queries = len(context.captured_queries)
        print(f"クエリ数: {num_queries}")

        # 期待値: select_related使用後は2クエリ以下
        # （1. DiaryEntry取得、2. student一括取得）
        assert num_queries <= 2, (
            f"N+1クエリが発生しています。クエリ数: {num_queries}件 "
            f"（期待値: 2件以下）"
        )


class TestTeacherNoteN1Queries(TestCase):
    """TeacherNote.__str__()のN+1クエリテスト"""

    def setUp(self):
        """テストデータ準備"""
        self.teacher = User.objects.create_user(
            username="teacher_note_001",
            email="teacher_note_001@example.com",
            first_name="花子",
            last_name="田中",
        )

        self.students = []
        for i in range(10):
            student = User.objects.create_user(
                username=f"student_note_{i:03d}",
                email=f"student_note_{i:03d}@example.com",
                first_name=f"太郎{i}",
                last_name=f"山田{i}",
            )
            self.students.append(student)

        # 担任メモ作成（10件）
        self.notes = []
        for i, student in enumerate(self.students):
            note = TeacherNote.objects.create(
                teacher=self.teacher, student=student, note=f"メモ{i}", is_shared=False
            )
            self.notes.append(note)

    def test_teacher_note_str_without_n1_queries(self):
        """TeacherNote.__str__()がN+1クエリを起こさないことを確認"""
        # Arrange
        notes = TeacherNote.objects.with_related()[:10]

        # Act & Assert
        with CaptureQueriesContext(connection) as context:
            for note in notes:
                _ = str(note)

        num_queries = len(context.captured_queries)
        print(f"クエリ数: {num_queries}")

        # 期待値: 3クエリ以下
        # （1. TeacherNote取得、2. teacher一括取得、3. student一括取得）
        assert num_queries <= 3, (
            f"N+1クエリが発生しています。クエリ数: {num_queries}件 "
            f"（期待値: 3件以下）"
        )


class TestDailyAttendanceN1Queries(TestCase):
    """DailyAttendance.__str__()のN+1クエリテスト"""

    def setUp(self):
        """テストデータ準備"""
        self.teacher = User.objects.create_user(
            username="teacher_attendance_001", email="teacher_attendance_001@example.com"
        )

        self.students = []
        for i in range(10):
            student = User.objects.create_user(
                username=f"student_attendance_{i:03d}",
                email=f"student_attendance_{i:03d}@example.com",
                first_name=f"太郎{i}",
                last_name=f"山田{i}",
            )
            self.students.append(student)

        self.classroom = ClassRoom.objects.create(
            grade=1, class_name="A", academic_year=2025, homeroom_teacher=self.teacher
        )

        # 出席記録作成（10件）
        self.attendances = []
        for student in self.students:
            attendance = DailyAttendance.objects.create(
                student=student,
                classroom=self.classroom,
                date="2025-10-19",
                status="present",
                noted_by=self.teacher,
            )
            self.attendances.append(attendance)

    def test_daily_attendance_str_without_n1_queries(self):
        """DailyAttendance.__str__()がN+1クエリを起こさないことを確認"""
        # Arrange
        attendances = DailyAttendance.objects.with_related()[:10]

        # Act & Assert
        with CaptureQueriesContext(connection) as context:
            for attendance in attendances:
                _ = str(attendance)

        num_queries = len(context.captured_queries)
        print(f"クエリ数: {num_queries}")

        # 期待値: 2クエリ以下
        assert num_queries <= 2, (
            f"N+1クエリが発生しています。クエリ数: {num_queries}件 "
            f"（期待値: 2件以下）"
        )


class TestTeacherNoteReadStatusN1Queries(TestCase):
    """TeacherNoteReadStatus.__str__()のN+1クエリテスト"""

    def setUp(self):
        """テストデータ準備"""
        self.teacher1 = User.objects.create_user(
            username="teacher_status_001",
            email="teacher_status_001@example.com",
            first_name="花子",
            last_name="田中",
        )
        self.teacher2 = User.objects.create_user(
            username="teacher_status_002",
            email="teacher_status_002@example.com",
            first_name="次郎",
            last_name="鈴木",
        )

        self.student = User.objects.create_user(
            username="student_status_001",
            email="student_status_001@example.com",
            first_name="太郎",
            last_name="山田",
        )

        # 担任メモ作成
        self.notes = []
        for i in range(10):
            note = TeacherNote.objects.create(
                teacher=self.teacher1,
                student=self.student,
                note=f"共有メモ{i}",
                is_shared=True,
            )
            self.notes.append(note)

            # 既読ステータス作成
            TeacherNoteReadStatus.objects.create(teacher=self.teacher2, note=note)

    def test_teacher_note_read_status_str_without_n1_queries(self):
        """TeacherNoteReadStatus.__str__()がN+1クエリを起こさないことを確認"""
        # Arrange
        read_statuses = TeacherNoteReadStatus.objects.with_related()[:10]

        # Act & Assert
        with CaptureQueriesContext(connection) as context:
            for status in read_statuses:
                _ = str(status)

        num_queries = len(context.captured_queries)
        print(f"クエリ数: {num_queries}")

        # 期待値: 3クエリ以下
        assert num_queries <= 3, (
            f"N+1クエリが発生しています。クエリ数: {num_queries}件 "
            f"（期待値: 3件以下）"
        )


class TestClassRoomAllTeachersN1Queries(TestCase):
    """ClassRoom.all_teachersプロパティのN+1クエリテスト"""

    def setUp(self):
        """テストデータ準備"""
        self.homeroom_teacher = User.objects.create_user(
            username="teacher_classroom_001", email="teacher_classroom_001@example.com"
        )

        self.assistant_teachers = []
        for i in range(1, 4):  # 1-3
            teacher = User.objects.create_user(
                username=f"assistant_teacher_{i:03d}", email=f"assistant_teacher_{i:03d}@example.com"
            )
            self.assistant_teachers.append(teacher)

        # クラス作成（10件）
        self.classrooms = []
        for i in range(10):
            classroom = ClassRoom.objects.create(
                grade=1,
                class_name=chr(65 + i),  # A, B, C, ...
                academic_year=2025,
                homeroom_teacher=self.homeroom_teacher,
            )
            classroom.assistant_teachers.set(self.assistant_teachers)
            self.classrooms.append(classroom)

    def test_all_teachers_property_without_n1_queries(self):
        """ClassRoom.all_teachersがN+1クエリを起こさないことを確認"""
        # Arrange
        classrooms = ClassRoom.objects.with_related()[:10]

        # Act & Assert
        with CaptureQueriesContext(connection) as context:
            for classroom in classrooms:
                _ = classroom.all_teachers

        num_queries = len(context.captured_queries)
        print(f"クエリ数: {num_queries}")

        # 期待値: 3クエリ以下
        # （1. ClassRoom取得、2. homeroom_teacher一括取得、
        #   3. assistant_teachers一括取得）
        assert num_queries <= 3, (
            f"N+1クエリが発生しています。クエリ数: {num_queries}件 "
            f"（期待値: 3件以下）"
        )

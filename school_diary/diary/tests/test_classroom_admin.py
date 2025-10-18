"""ClassRoom管理画面のテスト (TDD)

Phase 1: 管理画面フィルタ機能
- 担任フィールドには担任権限を持つユーザーのみ表示
- 生徒フィールドには生徒のみ表示

Phase 2: 副担任機能
- assistant_teachersフィールドの基本動作
- 副担任の権限チェック
- ヘルパーメソッド (all_teachers, is_teacher_of_class)

テスト実行方法:
    dj pytest school_diary/diary/tests/test_classroom_admin.py -v
"""

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.test import TestCase

from school_diary.diary.admin import ClassRoomAdmin
from school_diary.diary.models import ClassRoom

User = get_user_model()


class MockRequest:
    """管理画面テスト用のモックリクエスト"""

    def __init__(self, user):
        self.user = user


class ClassRoomAdminFilterTest(TestCase):
    """Phase 1: 管理画面フィルタ機能のテスト"""

    def setUp(self):
        """テストデータ準備"""
        # AdminSiteとAdminのインスタンス化
        self.site = AdminSite()
        self.admin = ClassRoomAdmin(ClassRoom, self.site)

        # テストユーザー作成
        self.student = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="password123",
            first_name="太郎",
            last_name="生徒",
        )
        self.student.profile.role = "student"
        self.student.profile.save()

        self.teacher = User.objects.create_user(
            username="teacher@example.com",
            email="teacher@example.com",
            password="password123",
            first_name="花子",
            last_name="担任",
        )
        self.teacher.profile.role = "teacher"
        self.teacher.profile.save()

        self.grade_leader = User.objects.create_user(
            username="grade_leader@example.com",
            email="grade_leader@example.com",
            password="password123",
            first_name="次郎",
            last_name="学年主任",
        )
        self.grade_leader.profile.role = "grade_leader"
        self.grade_leader.profile.managed_grade = 1
        self.grade_leader.profile.save()

        self.school_leader = User.objects.create_user(
            username="school_leader@example.com",
            email="school_leader@example.com",
            password="password123",
            first_name="三郎",
            last_name="校長",
        )
        self.school_leader.profile.role = "school_leader"
        self.school_leader.profile.save()

    def test_homeroom_teacher_filter_excludes_students(self):
        """担任フィールドに生徒が表示されないことを確認"""
        # モックリクエスト作成
        request = MockRequest(self.teacher)

        # ForeignKeyフィールドを取得
        db_field = ClassRoom._meta.get_field("homeroom_teacher")

        # formfield_for_foreignkeyを呼び出す
        form_field = self.admin.formfield_for_foreignkey(db_field, request)

        # querysetに生徒が含まれていないことを確認
        self.assertNotIn(self.student, form_field.queryset)

    def test_homeroom_teacher_filter_includes_teachers(self):
        """担任フィールドに担任が表示されることを確認"""
        request = MockRequest(self.teacher)
        db_field = ClassRoom._meta.get_field("homeroom_teacher")
        form_field = self.admin.formfield_for_foreignkey(db_field, request)

        # querysetに担任が含まれることを確認
        self.assertIn(self.teacher, form_field.queryset)

    def test_homeroom_teacher_filter_includes_grade_leaders(self):
        """担任フィールドに学年主任が表示されることを確認"""
        request = MockRequest(self.teacher)
        db_field = ClassRoom._meta.get_field("homeroom_teacher")
        form_field = self.admin.formfield_for_foreignkey(db_field, request)

        # querysetに学年主任が含まれることを確認
        self.assertIn(self.grade_leader, form_field.queryset)

    def test_homeroom_teacher_filter_includes_school_leaders(self):
        """担任フィールドに校長が表示されることを確認"""
        request = MockRequest(self.teacher)
        db_field = ClassRoom._meta.get_field("homeroom_teacher")
        form_field = self.admin.formfield_for_foreignkey(db_field, request)

        # querysetに校長が含まれることを確認
        self.assertIn(self.school_leader, form_field.queryset)

    def test_students_filter_includes_only_students(self):
        """生徒フィールドに生徒のみが表示されることを確認"""
        request = MockRequest(self.teacher)
        db_field = ClassRoom._meta.get_field("students")
        form_field = self.admin.formfield_for_manytomany(db_field, request)

        # querysetに生徒が含まれることを確認
        self.assertIn(self.student, form_field.queryset)

    def test_students_filter_excludes_teachers(self):
        """生徒フィールドに担任が表示されないことを確認"""
        request = MockRequest(self.teacher)
        db_field = ClassRoom._meta.get_field("students")
        form_field = self.admin.formfield_for_manytomany(db_field, request)

        # querysetに担任が含まれていないことを確認
        self.assertNotIn(self.teacher, form_field.queryset)
        self.assertNotIn(self.grade_leader, form_field.queryset)
        self.assertNotIn(self.school_leader, form_field.queryset)


class AssistantTeacherFieldTest(TestCase):
    """Phase 2: 副担任フィールドの基本動作テスト"""

    def setUp(self):
        """テストデータ準備"""
        # テストユーザー作成
        self.teacher1 = User.objects.create_user(
            username="teacher1@example.com",
            email="teacher1@example.com",
            password="password123",
            first_name="花子",
            last_name="主担任",
        )
        self.teacher1.profile.role = "teacher"
        self.teacher1.profile.save()

        self.teacher2 = User.objects.create_user(
            username="teacher2@example.com",
            email="teacher2@example.com",
            password="password123",
            first_name="太郎",
            last_name="副担任",
        )
        self.teacher2.profile.role = "teacher"
        self.teacher2.profile.save()

        self.teacher3 = User.objects.create_user(
            username="teacher3@example.com",
            email="teacher3@example.com",
            password="password123",
            first_name="次郎",
            last_name="副担任2",
        )
        self.teacher3.profile.role = "teacher"
        self.teacher3.profile.save()

        self.student = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="password123",
            first_name="三郎",
            last_name="生徒",
        )
        self.student.profile.role = "student"
        self.student.profile.save()

    def test_classroom_has_assistant_teachers_field(self):
        """ClassRoomモデルにassistant_teachersフィールドが存在することを確認"""
        classroom = ClassRoom.objects.create(
            grade=1,
            class_name="A",
            academic_year=2025,
            homeroom_teacher=self.teacher1,
        )

        # assistant_teachersフィールドが存在することを確認
        self.assertTrue(hasattr(classroom, "assistant_teachers"))

    def test_assistant_teachers_can_be_added(self):
        """副担任を追加できることを確認"""
        classroom = ClassRoom.objects.create(
            grade=1,
            class_name="A",
            academic_year=2025,
            homeroom_teacher=self.teacher1,
        )

        # 副担任を追加
        classroom.assistant_teachers.add(self.teacher2)

        # 副担任が追加されたことを確認
        self.assertIn(self.teacher2, classroom.assistant_teachers.all())
        self.assertEqual(classroom.assistant_teachers.count(), 1)

    def test_assistant_teachers_can_be_multiple(self):
        """複数の副担任を追加できることを確認"""
        classroom = ClassRoom.objects.create(
            grade=1,
            class_name="A",
            academic_year=2025,
            homeroom_teacher=self.teacher1,
        )

        # 複数の副担任を追加
        classroom.assistant_teachers.add(self.teacher2, self.teacher3)

        # 複数の副担任が追加されたことを確認
        self.assertEqual(classroom.assistant_teachers.count(), 2)
        self.assertIn(self.teacher2, classroom.assistant_teachers.all())
        self.assertIn(self.teacher3, classroom.assistant_teachers.all())

    def test_assistant_teachers_filter_in_admin(self):
        """管理画面で副担任フィールドに担任権限を持つユーザーのみ表示されることを確認"""
        from school_diary.diary.admin import ClassRoomAdmin
        from django.contrib.admin.sites import AdminSite

        site = AdminSite()
        admin = ClassRoomAdmin(ClassRoom, site)
        request = MockRequest(self.teacher1)

        # ManyToManyFieldを取得
        db_field = ClassRoom._meta.get_field("assistant_teachers")

        # formfield_for_manytomanyを呼び出す
        form_field = admin.formfield_for_manytomany(db_field, request)

        # querysetに担任が含まれることを確認
        self.assertIn(self.teacher1, form_field.queryset)
        self.assertIn(self.teacher2, form_field.queryset)
        self.assertIn(self.teacher3, form_field.queryset)

        # querysetに生徒が含まれないことを確認
        self.assertNotIn(self.student, form_field.queryset)


class AssistantTeacherHelperMethodsTest(TestCase):
    """Phase 2: ClassRoomモデルのヘルパーメソッドテスト"""

    def setUp(self):
        """テストデータ準備"""
        self.teacher1 = User.objects.create_user(
            username="teacher1@example.com",
            email="teacher1@example.com",
            password="password123",
        )
        self.teacher1.profile.role = "teacher"
        self.teacher1.profile.save()

        self.teacher2 = User.objects.create_user(
            username="teacher2@example.com",
            email="teacher2@example.com",
            password="password123",
        )
        self.teacher2.profile.role = "teacher"
        self.teacher2.profile.save()

        self.other_teacher = User.objects.create_user(
            username="other@example.com",
            email="other@example.com",
            password="password123",
        )
        self.other_teacher.profile.role = "teacher"
        self.other_teacher.profile.save()

        self.classroom = ClassRoom.objects.create(
            grade=1,
            class_name="A",
            academic_year=2025,
            homeroom_teacher=self.teacher1,
        )
        self.classroom.assistant_teachers.add(self.teacher2)

    def test_all_teachers_property(self):
        """all_teachersプロパティが主担任と副担任の全リストを返すことを確認"""
        teachers = self.classroom.all_teachers

        # 主担任と副担任が含まれることを確認
        self.assertIn(self.teacher1, teachers)
        self.assertIn(self.teacher2, teachers)
        self.assertEqual(len(teachers), 2)

    def test_all_teachers_property_without_assistant(self):
        """副担任がいない場合、all_teachersが主担任のみを返すことを確認"""
        classroom = ClassRoom.objects.create(
            grade=2,
            class_name="A",
            academic_year=2025,
            homeroom_teacher=self.teacher1,
        )

        teachers = classroom.all_teachers

        # 主担任のみが含まれることを確認
        self.assertIn(self.teacher1, teachers)
        self.assertEqual(len(teachers), 1)

    def test_is_teacher_of_class_homeroom_teacher(self):
        """is_teacher_of_classメソッドが主担任を正しく判定することを確認"""
        self.assertTrue(self.classroom.is_teacher_of_class(self.teacher1))

    def test_is_teacher_of_class_assistant_teacher(self):
        """is_teacher_of_classメソッドが副担任を正しく判定することを確認"""
        self.assertTrue(self.classroom.is_teacher_of_class(self.teacher2))

    def test_is_teacher_of_class_other_teacher(self):
        """is_teacher_of_classメソッドが他の担任を正しく判定することを確認"""
        self.assertFalse(self.classroom.is_teacher_of_class(self.other_teacher))


class AssistantTeacherPermissionsTest(TestCase):
    """Phase 2: 副担任の権限チェックテスト（DiaryEntryAdmin）"""

    def setUp(self):
        """テストデータ準備"""
        from school_diary.diary.admin import DiaryEntryAdmin
        from school_diary.diary.models import DiaryEntry
        from django.contrib.admin.sites import AdminSite

        # 担任・副担任・生徒を作成
        self.homeroom_teacher = User.objects.create_user(
            username="homeroom@example.com",
            email="homeroom@example.com",
            password="password123",
        )
        self.homeroom_teacher.profile.role = "teacher"
        self.homeroom_teacher.profile.save()

        self.assistant_teacher = User.objects.create_user(
            username="assistant@example.com",
            email="assistant@example.com",
            password="password123",
        )
        self.assistant_teacher.profile.role = "teacher"
        self.assistant_teacher.profile.save()

        self.student = User.objects.create_user(
            username="student@example.com",
            email="student@example.com",
            password="password123",
        )
        self.student.profile.role = "student"
        self.student.profile.save()

        # クラス作成（主担任 + 副担任）
        self.classroom = ClassRoom.objects.create(
            grade=1,
            class_name="A",
            academic_year=2025,
            homeroom_teacher=self.homeroom_teacher,
        )
        self.classroom.assistant_teachers.add(self.assistant_teacher)
        self.classroom.students.add(self.student)

        # 連絡帳エントリー作成
        self.diary_entry = DiaryEntry.objects.create(
            student=self.student,
            classroom=self.classroom,
            entry_date="2025-01-10",
            health_condition=3,
            mental_condition=3,
            reflection="テスト",
        )

        # DiaryEntryAdminのインスタンス化
        self.site = AdminSite()
        self.admin = DiaryEntryAdmin(DiaryEntry, self.site)

    def test_homeroom_teacher_can_view_diary_entries(self):
        """主担任が連絡帳を閲覧できることを確認"""
        request = MockRequest(self.homeroom_teacher)
        queryset = self.admin.get_queryset(request)

        # 主担任が自分のクラスの生徒の連絡帳を閲覧できる
        self.assertIn(self.diary_entry, queryset)

    def test_assistant_teacher_can_view_diary_entries(self):
        """副担任が連絡帳を閲覧できることを確認（重要テスト）"""
        request = MockRequest(self.assistant_teacher)
        queryset = self.admin.get_queryset(request)

        # 副担任が自分のクラスの生徒の連絡帳を閲覧できる
        self.assertIn(self.diary_entry, queryset)

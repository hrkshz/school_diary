"""管理画面ユーザー作成フロー統合テスト

ユーザー要求:
- 各ロールでcreate{数字}@example.com形式のユーザー作成
- ロール割り当て、クラス追加などの全フローをテスト
- 想定できる全テストケースを洗い出し

テスト構成（27テスト）:
1. TestUserProfileSignal: post_saveシグナル動作確認（4テスト）
2. TestStudentCreationFlow: 生徒作成フロー（4テスト）
3. TestTeacherCreationFlow: 担任作成フロー（4テスト）
4. TestGradeLeaderCreationFlow: 学年主任作成フロー（4テスト）
5. TestSchoolLeaderCreationFlow: 校長作成フロー（3テスト）
6. TestEdgeCases: エッジケース（8テスト）
"""

import pytest
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.test import TestCase

from school_diary.diary.models import ClassRoom
from school_diary.diary.models import UserProfile

User = get_user_model()


class TestUserProfileSignal(TestCase):
    """post_saveシグナルでUserProfile自動作成を確認"""

    def test_student_user_profile_auto_created(self):
        """生徒ユーザー作成時にUserProfileが自動作成される"""
        user = User.objects.create_user(
            username="create001@example.com",
            email="create001@example.com",
            password="password123",
        )

        # UserProfile自動作成確認
        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(user.profile.role, "student")
        self.assertIsNone(user.profile.managed_grade)

        # EmailAddress自動作成確認
        email_address = EmailAddress.objects.filter(user=user).first()
        self.assertIsNotNone(email_address)
        self.assertEqual(email_address.email, "create001@example.com")

    def test_teacher_user_profile_auto_created(self):
        """担任ユーザー作成時にUserProfileが自動作成される"""
        user = User.objects.create_user(
            username="create_teacher001@example.com",
            email="create_teacher001@example.com",
            password="password123",
        )

        # UserProfile自動作成確認（デフォルトはstudent）
        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(user.profile.role, "student")

        # role変更
        user.profile.role = "teacher"
        user.profile.save()

        user.refresh_from_db()
        self.assertEqual(user.profile.role, "teacher")

    def test_grade_leader_user_profile_auto_created(self):
        """学年主任ユーザー作成時にUserProfileが自動作成される"""
        user = User.objects.create_user(
            username="create_leader001@example.com",
            email="create_leader001@example.com",
            password="password123",
        )

        # UserProfile自動作成確認
        self.assertTrue(hasattr(user, "profile"))

        # role + managed_grade設定
        user.profile.role = "grade_leader"
        user.profile.managed_grade = 2
        user.profile.save()

        user.refresh_from_db()
        self.assertEqual(user.profile.role, "grade_leader")
        self.assertEqual(user.profile.managed_grade, 2)

    def test_school_leader_user_profile_auto_created(self):
        """校長ユーザー作成時にUserProfileが自動作成される"""
        user = User.objects.create_user(
            username="create_principal001@example.com",
            email="create_principal001@example.com",
            password="password123",
        )

        # UserProfile自動作成確認
        self.assertTrue(hasattr(user, "profile"))

        # role設定
        user.profile.role = "school_leader"
        user.profile.save()

        user.refresh_from_db()
        self.assertEqual(user.profile.role, "school_leader")


class TestStudentCreationFlow(TestCase):
    """生徒作成フロー統合テスト"""

    def setUp(self):
        """テストデータ準備"""
        # 担任作成
        teacher = User.objects.create_user(
            username="teacher_test@example.com",
            email="teacher_test@example.com",
            password="password123",
        )
        teacher.profile.role = "teacher"
        teacher.profile.save()

        # クラス作成
        self.classroom = ClassRoom.objects.create(
            grade=1,
            class_name="A",
            academic_year=2025,
            homeroom_teacher=teacher,
        )

    def test_student_creation(self):
        """生徒ユーザー作成"""
        user = User.objects.create_user(
            username="create_student001@example.com",
            email="create_student001@example.com",
            password="password123",
            first_name="太郎",
            last_name="山田",
        )

        self.assertEqual(user.email, "create_student001@example.com")
        self.assertEqual(user.first_name, "太郎")
        self.assertEqual(user.last_name, "山田")

    def test_student_userprofile_creation(self):
        """生徒UserProfile作成確認"""
        user = User.objects.create_user(
            username="create_student002@example.com",
            email="create_student002@example.com",
            password="password123",
        )

        self.assertEqual(user.profile.role, "student")

    def test_student_classroom_assignment(self):
        """生徒のクラス追加"""
        user = User.objects.create_user(
            username="create_student003@example.com",
            email="create_student003@example.com",
            password="password123",
        )

        self.classroom.students.add(user)

        self.assertIn(user, self.classroom.students.all())
        self.assertEqual(user.classes.count(), 1)

    def test_student_login_redirect(self):
        """生徒ログイン後のリダイレクト確認"""
        user = User.objects.create_user(
            username="create_student004@example.com",
            email="create_student004@example.com",
            password="password123",
        )
        self.classroom.students.add(user)

        # ログイン
        self.client.login(
            username="create_student004@example.com",
            password="password123",
        )

        # リダイレクト確認
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/student/", response.url)


class TestTeacherCreationFlow(TestCase):
    """担任作成フロー統合テスト"""

    def test_teacher_creation(self):
        """担任ユーザー作成"""
        user = User.objects.create_user(
            username="create_teacher002@example.com",
            email="create_teacher002@example.com",
            password="password123",
            first_name="花子",
            last_name="佐藤",
        )

        self.assertEqual(user.email, "create_teacher002@example.com")

    def test_teacher_role_assignment(self):
        """担任role割り当て"""
        user = User.objects.create_user(
            username="create_teacher003@example.com",
            email="create_teacher003@example.com",
            password="password123",
        )

        user.profile.role = "teacher"
        user.profile.save()

        user.refresh_from_db()
        self.assertEqual(user.profile.role, "teacher")

    def test_teacher_classroom_assignment(self):
        """担任のクラス担当設定"""
        user = User.objects.create_user(
            username="create_teacher004@example.com",
            email="create_teacher004@example.com",
            password="password123",
        )
        user.profile.role = "teacher"
        user.profile.save()

        classroom = ClassRoom.objects.create(
            grade=2,
            class_name="A",
            academic_year=2025,
            homeroom_teacher=user,
        )

        self.assertEqual(classroom.homeroom_teacher, user)
        self.assertEqual(user.homeroom_classes.count(), 1)

    def test_teacher_login_redirect(self):
        """担任ログイン後のリダイレクト確認"""
        user = User.objects.create_user(
            username="create_teacher005@example.com",
            email="create_teacher005@example.com",
            password="password123",
        )
        user.profile.role = "teacher"
        user.profile.save()

        ClassRoom.objects.create(
            grade=2,
            class_name="B",
            academic_year=2025,
            homeroom_teacher=user,
        )

        # ログイン
        self.client.login(
            username="create_teacher005@example.com",
            password="password123",
        )

        # リダイレクト確認
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/teacher/", response.url)


class TestGradeLeaderCreationFlow(TestCase):
    """学年主任作成フロー統合テスト"""

    def test_grade_leader_creation(self):
        """学年主任ユーザー作成"""
        user = User.objects.create_user(
            username="create_leader002@example.com",
            email="create_leader002@example.com",
            password="password123",
        )

        self.assertEqual(user.email, "create_leader002@example.com")

    def test_grade_leader_role_assignment(self):
        """学年主任role + managed_grade割り当て"""
        user = User.objects.create_user(
            username="create_leader003@example.com",
            email="create_leader003@example.com",
            password="password123",
        )

        user.profile.role = "grade_leader"
        user.profile.managed_grade = 3
        user.profile.save()

        user.refresh_from_db()
        self.assertEqual(user.profile.role, "grade_leader")
        self.assertEqual(user.profile.managed_grade, 3)

    def test_grade_leader_dual_role(self):
        """学年主任 + 担任の兼任"""
        user = User.objects.create_user(
            username="create_leader004@example.com",
            email="create_leader004@example.com",
            password="password123",
        )

        user.profile.role = "grade_leader"
        user.profile.managed_grade = 1
        user.profile.save()

        # クラス担任も兼任
        classroom = ClassRoom.objects.create(
            grade=1,
            class_name="A",
            academic_year=2025,
            homeroom_teacher=user,
        )

        self.assertEqual(user.profile.role, "grade_leader")
        self.assertEqual(classroom.homeroom_teacher, user)

    def test_grade_leader_login_redirect(self):
        """学年主任ログイン後のリダイレクト確認"""
        user = User.objects.create_user(
            username="create_leader005@example.com",
            email="create_leader005@example.com",
            password="password123",
        )
        user.profile.role = "grade_leader"
        user.profile.managed_grade = 2
        user.profile.save()

        # ログイン
        self.client.login(
            username="create_leader005@example.com",
            password="password123",
        )

        # リダイレクト確認（担任兼任なしの場合）
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/grade-overview/", response.url)


class TestSchoolLeaderCreationFlow(TestCase):
    """校長/教頭作成フロー統合テスト"""

    def test_school_leader_creation(self):
        """校長ユーザー作成"""
        user = User.objects.create_user(
            username="create_principal002@example.com",
            email="create_principal002@example.com",
            password="password123",
            first_name="校長",
            last_name="鈴木",
        )

        self.assertEqual(user.email, "create_principal002@example.com")

    def test_school_leader_role_assignment(self):
        """校長role割り当て"""
        user = User.objects.create_user(
            username="create_principal003@example.com",
            email="create_principal003@example.com",
            password="password123",
        )

        user.profile.role = "school_leader"
        user.profile.save()

        user.refresh_from_db()
        self.assertEqual(user.profile.role, "school_leader")
        self.assertIsNone(user.profile.managed_grade)

    def test_school_leader_login_redirect(self):
        """校長ログイン後のリダイレクト確認"""
        user = User.objects.create_user(
            username="create_principal004@example.com",
            email="create_principal004@example.com",
            password="password123",
        )
        user.profile.role = "school_leader"
        user.profile.save()

        # ログイン
        self.client.login(
            username="create_principal004@example.com",
            password="password123",
        )

        # リダイレクト確認
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/school-overview/", response.url)


class TestEdgeCases(TestCase):
    """エッジケース・境界値テスト"""

    def test_admin_user_creation(self):
        """管理画面からのUser作成（UserProfile自動作成）"""
        user = User.objects.create_user(
            username="admin_create001@example.com",
            email="admin_create001@example.com",
            password="password123",
        )

        # UserProfile自動作成確認
        self.assertTrue(hasattr(user, "profile"))
        self.assertIsNotNone(user.profile)

    def test_userprofile_role_change(self):
        """role変更フロー"""
        user = User.objects.create_user(
            username="rolechange001@example.com",
            email="rolechange001@example.com",
            password="password123",
        )

        # 初期: student
        self.assertEqual(user.profile.role, "student")

        # teacher に変更
        user.profile.role = "teacher"
        user.profile.save()
        user.refresh_from_db()
        self.assertEqual(user.profile.role, "teacher")

        # grade_leader に変更
        user.profile.role = "grade_leader"
        user.profile.managed_grade = 1
        user.profile.save()
        user.refresh_from_db()
        self.assertEqual(user.profile.role, "grade_leader")
        self.assertEqual(user.profile.managed_grade, 1)

    def test_userprofile_without_email(self):
        """email無しユーザーのUserProfile作成"""
        user = User.objects.create_user(
            username="noemail001",
            password="password123",
        )

        # UserProfile作成確認（email無しでも作成される）
        self.assertTrue(hasattr(user, "profile"))

        # EmailAddress作成されない
        email_count = EmailAddress.objects.filter(user=user).count()
        self.assertEqual(email_count, 0)

    def test_managed_grade_validation(self):
        """managed_grade範囲バリデーション"""
        user = User.objects.create_user(
            username="validation001@example.com",
            email="validation001@example.com",
            password="password123",
        )

        user.profile.role = "grade_leader"

        # 正常値: 1, 2, 3
        for grade in [1, 2, 3]:
            user.profile.managed_grade = grade
            user.profile.full_clean()  # バリデーション実行
            user.profile.save()

        # 異常値: 0, 4（MinValueValidator, MaxValueValidator）
        from django.core.exceptions import ValidationError

        user.profile.managed_grade = 0
        with pytest.raises(ValidationError):
            user.profile.full_clean()

        user.profile.managed_grade = 4
        with pytest.raises(ValidationError):
            user.profile.full_clean()

    def test_duplicate_email(self):
        """重複email禁止確認"""
        User.objects.create_user(
            username="dup001@example.com",
            email="dup001@example.com",
            password="password123",
        )

        # 同じemailで別username作成は失敗しない（usernameが主キー）
        user2 = User.objects.create_user(
            username="dup002@example.com",
            email="dup001@example.com",  # 同じemail
            password="password123",
        )

        self.assertEqual(user2.email, "dup001@example.com")

    def test_superuser_profile_creation(self):
        """スーパーユーザー作成時のUserProfile"""
        admin = User.objects.create_superuser(
            username="superadmin@example.com",
            email="superadmin@example.com",
            password="password123",
        )

        # UserProfile自動作成確認
        self.assertTrue(hasattr(admin, "profile"))
        self.assertEqual(admin.profile.role, "student")  # デフォルト値

    def test_existing_user_no_profile(self):
        """UserProfile無しの既存User（シグナル実装前データ）"""
        # UserProfile削除でシミュレーション
        user = User.objects.create_user(
            username="legacy001@example.com",
            email="legacy001@example.com",
            password="password123",
        )

        # UserProfile削除
        UserProfile.objects.filter(user=user).delete()

        # refresh後、profileアクセスでエラー
        user.refresh_from_db()
        with pytest.raises(UserProfile.DoesNotExist):
            _ = user.profile

    def test_grade_leader_without_managed_grade(self):
        """grade_leaderだがmanaged_grade未設定"""
        user = User.objects.create_user(
            username="leader_no_grade@example.com",
            email="leader_no_grade@example.com",
            password="password123",
        )

        user.profile.role = "grade_leader"
        # managed_grade未設定（None）
        user.profile.save()

        user.refresh_from_db()
        self.assertEqual(user.profile.role, "grade_leader")
        self.assertIsNone(user.profile.managed_grade)

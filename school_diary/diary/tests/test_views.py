"""Views層の統合テスト

カバレッジ向上とCritical Gap（S-02要件）対応のため作成。
views.py 40% → 70% を目標。

テスト範囲:
- DiaryEntryCreateView: 作成機能
- DiaryEntryUpdateView: 編集機能（S-02要件: 既読後編集不可）
- 権限チェック: ロールベースアクセス制御
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DiaryEntry
from school_diary.diary.utils import get_previous_school_day

User = get_user_model()


@pytest.fixture
def classroom(db):
    """テスト用クラスルーム"""
    return ClassRoom.objects.create(
        class_name="A",
        grade=1,
        academic_year=2025,
    )


@pytest.fixture
def teacher(db, classroom):
    """テスト用担任"""
    user = User.objects.create_user(
        username="teacher@test.com",
        email="teacher@test.com",
        password="password123",
    )
    user.profile.role = "teacher"
    user.profile.save()
    classroom.homeroom_teacher = user
    classroom.save()
    return user


@pytest.fixture
def student(db, classroom):
    """テスト用生徒"""
    user = User.objects.create_user(
        username="student@test.com",
        email="student@test.com",
        password="password123",
    )
    user.profile.classroom = classroom
    user.profile.save()
    return user


@pytest.fixture
def other_student(db, classroom):
    """別の生徒（権限チェック用）"""
    user = User.objects.create_user(
        username="other_student@test.com",
        email="other_student@test.com",
        password="password123",
    )
    user.profile.classroom = classroom
    user.profile.save()
    return user


@pytest.mark.django_db
class TestDiaryEntryCreateView:
    """連絡帳作成ビューのテスト"""

    def test_create_entry_success(self, student):
        """正常系: 連絡帳作成成功"""
        client = Client()
        client.force_login(student)

        url = reverse("diary:diary_create")
        # 連絡帳は「前登校日の振り返り」（土日除く）
        previous_school_day = get_previous_school_day(timezone.now().date())
        data = {
            "entry_date": previous_school_day.isoformat(),
            "health_condition": 4,
            "mental_condition": 5,
            "reflection": "テスト振り返り",
        }

        response = client.post(url, data)

        assert response.status_code == 302  # リダイレクト
        assert DiaryEntry.objects.filter(student=student).exists()

    def test_create_entry_validation_error_invalid_health(self, student):
        """異常系: 不正なhealth_condition（境界値外）"""
        client = Client()
        client.force_login(student)

        url = reverse("diary:diary_create")
        data = {
            "entry_date": timezone.now().date(),
            "health_condition": 6,  # 不正値（1-5のみ許可）
            "mental_condition": 5,
            "reflection": "テスト",
        }

        response = client.post(url, data)

        assert response.status_code == 200  # フォームエラーで再表示
        assert not DiaryEntry.objects.filter(student=student).exists()

    def test_create_entry_duplicate_date_error(self, student):
        """異常系: 重複日付エラー（UNIQUE制約）"""
        client = Client()
        client.force_login(student)

        entry_date = timezone.now().date()

        # 1件目作成
        DiaryEntry.objects.create(
            student=student,
            entry_date=entry_date,
            health_condition=4,
            mental_condition=5,
            reflection="1件目",
        )

        # 2件目（重複）試行
        url = reverse("diary:diary_create")
        data = {
            "entry_date": entry_date,
            "health_condition": 4,
            "mental_condition": 5,
            "reflection": "2件目（重複）",
        }

        response = client.post(url, data)

        assert response.status_code == 200  # エラーで再表示
        assert DiaryEntry.objects.filter(student=student).count() == 1

    def test_create_entry_unauthenticated_redirect(self):
        """セキュリティ: 未認証ユーザーはログインページへリダイレクト"""
        client = Client()

        url = reverse("diary:diary_create")
        response = client.get(url)

        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.django_db
class TestDiaryEntryUpdateView:
    """連絡帳編集ビューのテスト（S-02要件）"""

    def test_update_entry_before_read_success(self, student):
        """S-02要件: 既読前は編集可能"""
        client = Client()
        client.force_login(student)

        # エントリー作成（未既読）
        previous_school_day = get_previous_school_day(timezone.now().date())
        entry = DiaryEntry.objects.create(
            student=student,
            entry_date=previous_school_day,
            health_condition=4,
            mental_condition=5,
            reflection="初回内容",
        )

        # 編集試行
        url = reverse("diary:diary_update", kwargs={"pk": entry.pk})
        data = {
            "entry_date": entry.entry_date.isoformat(),
            "health_condition": 3,
            "mental_condition": 4,
            "reflection": "編集後の内容",
        }

        response = client.post(url, data)

        assert response.status_code == 302  # 成功リダイレクト
        entry.refresh_from_db()
        assert entry.reflection == "編集後の内容"

    def test_update_entry_after_read_forbidden(self, student, teacher):
        """S-02要件（Critical Gap）: 既読後は編集不可"""
        client = Client()
        client.force_login(student)

        # エントリー作成
        previous_school_day = get_previous_school_day(timezone.now().date())
        entry = DiaryEntry.objects.create(
            student=student,
            entry_date=previous_school_day,
            health_condition=4,
            mental_condition=5,
            reflection="初回内容",
        )

        # 担任が既読処理
        entry.is_read = True
        entry.read_by = teacher
        entry.read_at = timezone.now()
        entry.save()

        # 生徒が編集試行（既読後）
        url = reverse("diary:diary_update", kwargs={"pk": entry.pk})
        data = {
            "entry_date": entry.entry_date,
            "health_condition": 3,
            "mental_condition": 4,
            "reflection": "編集試行（既読後）",
        }

        response = client.post(url, data)

        # 実装は get_queryset() で is_read=False でフィルタしているため 404
        assert response.status_code == 404
        entry.refresh_from_db()
        assert entry.reflection == "初回内容"  # 編集されていないことを確認

    def test_update_other_student_entry_forbidden(self, student, other_student):
        """セキュリティ: 他人のエントリーは編集不可"""
        # other_studentのエントリー作成
        previous_school_day = get_previous_school_day(timezone.now().date())
        entry = DiaryEntry.objects.create(
            student=other_student,
            entry_date=previous_school_day,
            health_condition=4,
            mental_condition=5,
            reflection="他人のエントリー",
        )

        # studentが編集試行
        client = Client()
        client.force_login(student)

        url = reverse("diary:diary_update", kwargs={"pk": entry.pk})
        data = {
            "entry_date": entry.entry_date,
            "health_condition": 3,
            "mental_condition": 4,
            "reflection": "不正編集試行",
        }

        response = client.post(url, data)

        # 実装は get_queryset() で student=self.request.user でフィルタしているため 404
        assert response.status_code == 404
        entry.refresh_from_db()
        assert entry.reflection == "他人のエントリー"


@pytest.mark.django_db
class TestTeacherDashboardPermissions:
    """担任ダッシュボードの権限チェック"""

    def test_teacher_can_view_assigned_class_only(self, teacher, classroom):
        """セキュリティ: 担任は担当クラスのみ閲覧可能"""
        client = Client()
        client.force_login(teacher)

        url = reverse("diary:teacher_dashboard")
        response = client.get(url)

        assert response.status_code == 200
        assert classroom.class_name in str(response.content)

    def test_teacher_cannot_view_other_class(self, teacher):
        """セキュリティ: 他のクラスの生徒データは閲覧不可"""
        # 別のクラスを作成
        other_classroom = ClassRoom.objects.create(
            class_name="B",
            grade=1,
            academic_year=2025,
        )

        other_student = User.objects.create_user(
            username="other_class_student@test.com",
            email="other_class_student@test.com",
            password="password123",
        )
        other_student.profile.classroom = other_classroom
        other_student.profile.save()

        # 担任ダッシュボードにアクセス
        client = Client()
        client.force_login(teacher)

        url = reverse("diary:teacher_dashboard")
        response = client.get(url)

        # 他クラスの生徒は表示されない
        assert other_student.username not in str(response.content)


@pytest.mark.django_db
class TestStudentDashboardPermissions:
    """生徒ダッシュボードの権限チェック"""

    def test_student_can_view_own_entries_only(self, student, other_student):
        """セキュリティ: 生徒は自分のデータのみ閲覧可能"""
        # 自分のエントリー作成
        previous_school_day = get_previous_school_day(timezone.now().date())
        DiaryEntry.objects.create(
            student=student,
            entry_date=previous_school_day,
            health_condition=4,
            mental_condition=5,
            reflection="自分のエントリー",
        )

        # 他人のエントリー作成
        DiaryEntry.objects.create(
            student=other_student,
            entry_date=previous_school_day,
            health_condition=3,
            mental_condition=3,
            reflection="他人のエントリー",
        )

        # ダッシュボードアクセス
        client = Client()
        client.force_login(student)

        url = reverse("diary:student_dashboard")
        response = client.get(url)

        assert response.status_code == 200
        content = response.content.decode("utf-8")
        # 自分のエントリーは表示される
        assert "自分のエントリー" in content
        # 他人のエントリーは表示されない
        assert "他人のエントリー" not in content


@pytest.mark.django_db
class TestCardTriageEndpoints:
    """カードトリアージエンドポイントのテスト（AJAX）"""

    def test_mark_as_read_quick_success(self, teacher, student, classroom):
        """✓既読ボタン: 正常系（カードから既読のみ）"""
        from school_diary.diary.models import ActionStatus

        # クラスに生徒を追加
        classroom.students.add(student)

        # 未読エントリー作成
        previous_school_day = get_previous_school_day(timezone.now().date())
        entry = DiaryEntry.objects.create(
            student=student,
            entry_date=previous_school_day,
            health_condition=4,
            mental_condition=3,
            reflection="テスト",
            is_read=False,
        )

        # AJAX POSTリクエスト
        client = Client()
        client.force_login(teacher)

        url = reverse("diary:teacher_mark_as_read_quick", kwargs={"diary_id": entry.id})
        response = client.post(url, content_type="application/json")

        # レスポンス確認
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "success"

        # エントリー更新確認
        entry.refresh_from_db()
        assert entry.is_read is True
        assert entry.read_by == teacher
        assert entry.action_status == ActionStatus.NOT_REQUIRED

    def test_mark_as_read_quick_permission_denied(self, teacher, student, classroom):
        """✓既読ボタン: 権限エラー（他クラスの生徒）"""
        # 別のクラス作成
        other_classroom = ClassRoom.objects.create(
            class_name="B",
            grade=1,
            academic_year=2025,
        )
        other_student = User.objects.create_user(
            username="other_student_2@test.com",
            email="other_student_2@test.com",
            password="password123",
        )
        other_classroom.students.add(other_student)

        # 他クラスの生徒のエントリー作成
        previous_school_day = get_previous_school_day(timezone.now().date())
        entry = DiaryEntry.objects.create(
            student=other_student,
            entry_date=previous_school_day,
            health_condition=4,
            mental_condition=3,
            reflection="テスト",
            is_read=False,
        )

        # AJAX POSTリクエスト
        client = Client()
        client.force_login(teacher)

        url = reverse("diary:teacher_mark_as_read_quick", kwargs={"diary_id": entry.id})
        response = client.post(url, content_type="application/json")

        # 404エラー（get_object_or_404）
        assert response.status_code == 404

    def test_mark_as_read_quick_get_method_not_allowed(self, teacher, student, classroom):
        """✓既読ボタン: GETメソッドは405エラー"""
        classroom.students.add(student)

        previous_school_day = get_previous_school_day(timezone.now().date())
        entry = DiaryEntry.objects.create(
            student=student,
            entry_date=previous_school_day,
            health_condition=4,
            mental_condition=3,
            reflection="テスト",
        )

        client = Client()
        client.force_login(teacher)

        url = reverse("diary:teacher_mark_as_read_quick", kwargs={"diary_id": entry.id})
        response = client.get(url)  # GET メソッド

        assert response.status_code == 405

    def test_create_task_from_card_success(self, teacher, student, classroom):
        """📋タスクボタン: 正常系（カードからタスク化）"""
        from school_diary.diary.models import ActionStatus
        from school_diary.diary.models import InternalAction

        classroom.students.add(student)

        # 未読エントリー作成
        previous_school_day = get_previous_school_day(timezone.now().date())
        entry = DiaryEntry.objects.create(
            student=student,
            entry_date=previous_school_day,
            health_condition=4,
            mental_condition=2,
            reflection="テスト",
            is_read=False,
        )

        # AJAX POSTリクエスト
        client = Client()
        client.force_login(teacher)

        url = reverse("diary:teacher_create_task_from_card", kwargs={"diary_id": entry.id})
        response = client.post(
            url,
            {"internal_action": InternalAction.NEEDS_FOLLOW_UP},
        )

        # レスポンス確認
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "success"

        # エントリー更新確認
        entry.refresh_from_db()
        assert entry.is_read is True
        assert entry.read_by == teacher
        assert entry.internal_action == InternalAction.NEEDS_FOLLOW_UP
        assert entry.action_status == ActionStatus.IN_PROGRESS

    def test_create_task_from_card_missing_internal_action(self, teacher, student, classroom):
        """📋タスクボタン: internal_action未指定で400エラー"""
        classroom.students.add(student)

        previous_school_day = get_previous_school_day(timezone.now().date())
        entry = DiaryEntry.objects.create(
            student=student,
            entry_date=previous_school_day,
            health_condition=4,
            mental_condition=3,
            reflection="テスト",
        )

        client = Client()
        client.force_login(teacher)

        url = reverse("diary:teacher_create_task_from_card", kwargs={"diary_id": entry.id})
        response = client.post(url)  # internal_action未指定

        # 400エラー
        assert response.status_code == 400
        json_data = response.json()
        assert json_data["status"] == "error"

    def test_create_task_from_card_permission_denied(self, teacher, student, classroom):
        """📋タスクボタン: 権限エラー（他クラスの生徒）"""
        # 別のクラス作成
        other_classroom = ClassRoom.objects.create(
            class_name="C",
            grade=1,
            academic_year=2025,
        )
        other_student = User.objects.create_user(
            username="other_student_3@test.com",
            email="other_student_3@test.com",
            password="password123",
        )
        other_classroom.students.add(other_student)

        # 他クラスの生徒のエントリー作成
        previous_school_day = get_previous_school_day(timezone.now().date())
        entry = DiaryEntry.objects.create(
            student=other_student,
            entry_date=previous_school_day,
            health_condition=4,
            mental_condition=3,
            reflection="テスト",
        )

        client = Client()
        client.force_login(teacher)

        url = reverse("diary:teacher_create_task_from_card", kwargs={"diary_id": entry.id})
        response = client.post(url, {"internal_action": "needs_follow_up"})

        # 404エラー（get_object_or_404）
        assert response.status_code == 404

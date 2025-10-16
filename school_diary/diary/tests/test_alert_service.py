"""Tests for alert_service module (Inbox Pattern backend)

TDD Implementation:
- Red: Write failing tests first
- Green: Implement minimal code to pass
- Refactor: Optimize for N+1 problem
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model

from school_diary.diary.models import DiaryEntry, ClassRoom
from school_diary.diary import alert_service

User = get_user_model()


@pytest.fixture
def setup_classroom(db):
    """テスト用のクラスルームと生徒を作成"""
    # クラスルーム作成
    classroom = ClassRoom.objects.create(
        class_name="A",
        grade=1,
        academic_year=2025
    )

    # 担任作成
    teacher = User.objects.create_user(
        username="teacher@example.com",
        email="teacher@example.com",
        password="password123",
        first_name="太郎",
        last_name="先生"
    )
    teacher.profile.role = "teacher"
    teacher.profile.save()
    classroom.homeroom_teacher = teacher
    classroom.save()

    # 生徒3名作成
    students = []
    for i in range(3):
        student = User.objects.create_user(
            username=f"student{i+1}@example.com",
            email=f"student{i+1}@example.com",
            password="password123",
            first_name=f"生徒{i+1}",
            last_name="テスト"
        )
        student.profile.role = "student"
        student.profile.save()
        classroom.students.add(student)
        students.append(student)

    return {
        'classroom': classroom,
        'teacher': teacher,
        'students': students
    }


@pytest.mark.django_db
class TestClassifyStudents:
    """classify_students() のテスト（3段階分類）"""

    def test_classify_critical_mental_star_1(self, setup_classroom):
        """メンタル★1の生徒はcriticalに分類される"""
        classroom = setup_classroom['classroom']
        student = setup_classroom['students'][0]
        today = timezone.now().date()

        # メンタル★1のエントリー作成
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=1,  # ★1 = Critical
            reflection="つらい"
        )

        result = alert_service.classify_students(classroom)

        assert student in result['critical']
        assert student not in result['high']
        assert student not in result['normal']

    def test_classify_high_mental_star_2(self, setup_classroom):
        """メンタル★★の生徒はhighに分類される"""
        classroom = setup_classroom['classroom']
        student = setup_classroom['students'][0]
        today = timezone.now().date()

        # メンタル★★のエントリー作成
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=2,  # ★★ = High
            reflection="少し不安"
        )

        result = alert_service.classify_students(classroom)

        assert student not in result['critical']
        assert student in result['high']
        assert student not in result['normal']

    def test_classify_normal_healthy(self, setup_classroom):
        """体調・メンタルが良好な生徒はnormalに分類される"""
        classroom = setup_classroom['classroom']
        student = setup_classroom['students'][0]
        today = timezone.now().date()

        # 健康なエントリー作成
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=5,  # ★★★★★
            mental_condition=5,  # ★★★★★
            reflection="元気です"
        )

        result = alert_service.classify_students(classroom)

        assert student not in result['critical']
        assert student not in result['high']
        assert student in result['normal']

    def test_classify_no_entry_yesterday(self, setup_classroom):
        """昨日未提出の生徒はhighに分類される"""
        classroom = setup_classroom['classroom']
        student = setup_classroom['students'][0]
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        # 2日前のエントリーのみ（昨日は未提出）
        DiaryEntry.objects.create(
            student=student,
            entry_date=yesterday - timedelta(days=1),
            health_condition=4,
            mental_condition=4,
            reflection="元気"
        )

        result = alert_service.classify_students(classroom)

        # 昨日未提出 = high
        assert student not in result['critical']
        assert student in result['high']
        assert student not in result['normal']

    def test_classify_multiple_students(self, setup_classroom):
        """複数の生徒が正しく分類される"""
        classroom = setup_classroom['classroom']
        students = setup_classroom['students']
        today = timezone.now().date()

        # 生徒1: Critical（メンタル★1）
        DiaryEntry.objects.create(
            student=students[0],
            entry_date=today,
            health_condition=4,
            mental_condition=1,
            reflection="つらい"
        )

        # 生徒2: High（メンタル★★）
        DiaryEntry.objects.create(
            student=students[1],
            entry_date=today,
            health_condition=4,
            mental_condition=2,
            reflection="少し不安"
        )

        # 生徒3: Normal（健康）
        DiaryEntry.objects.create(
            student=students[2],
            entry_date=today,
            health_condition=5,
            mental_condition=5,
            reflection="元気"
        )

        result = alert_service.classify_students(classroom)

        assert students[0] in result['critical']
        assert students[1] in result['high']
        assert students[2] in result['normal']

    def test_no_n_plus_one_problem(self, setup_classroom, django_assert_num_queries):
        """N+1問題が発生しないことを確認（クエリ数=2）"""
        classroom = setup_classroom['classroom']
        students = setup_classroom['students']
        today = timezone.now().date()

        # 全生徒にエントリー作成
        for student in students:
            DiaryEntry.objects.create(
                student=student,
                entry_date=today,
                health_condition=4,
                mental_condition=3,
                reflection="普通"
            )

        # クエリ数を確認（生徒数に関わらず2クエリ）
        # Query 1: DiaryEntry一括取得（select_related('student')）
        # Query 2: classroom.students.all()
        with django_assert_num_queries(2):
            alert_service.classify_students(classroom)


@pytest.mark.django_db
class TestFormatInlineHistory:
    """format_inline_history() のテスト（直近3日の履歴表示）"""

    def test_format_inline_history_3_days(self, setup_classroom):
        """直近3日の履歴が正しくフォーマットされる"""
        student = setup_classroom['students'][0]
        today = timezone.now().date()

        # 3日分のエントリー作成
        entries = []
        for i in range(3):
            date = today - timedelta(days=2-i)
            entry = DiaryEntry.objects.create(
                student=student,
                entry_date=date,
                health_condition=4 - i,  # 4, 3, 2（低下）
                mental_condition=4 - i,
                reflection=f"Day {i}"
            )
            entries.append(entry)

        result = alert_service.format_inline_history(entries)

        # "10/14(★★★★)→10/15(★★★)→10/16(★★)" 形式
        assert "→" in result
        assert result.count("→") == 2  # 2つの矢印
        assert "★" in result


@pytest.mark.django_db
class TestGetSnippet:
    """get_snippet() のテスト（連絡帳スニペット生成）"""

    def test_get_snippet_short_text(self, setup_classroom):
        """50文字以下のテキストはそのまま返す"""
        student = setup_classroom['students'][0]
        today = timezone.now().date()

        entry = DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=3,
            reflection="今日は元気です。"
        )

        result = alert_service.get_snippet(entry)

        assert result == "今日は元気です。"

    def test_get_snippet_long_text(self, setup_classroom):
        """50文字を超えるテキストは省略される"""
        student = setup_classroom['students'][0]
        today = timezone.now().date()

        long_text = "今日は部活で先輩に怒られてしまいました。理由がよく分からないのでとても悲しいです。明日はもっと頑張りたいです。"
        entry = DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=3,
            reflection=long_text
        )

        result = alert_service.get_snippet(entry)

        assert len(result) <= 53  # 50文字 + "..."
        assert result.endswith("...")
        assert result.startswith("今日は部活で")

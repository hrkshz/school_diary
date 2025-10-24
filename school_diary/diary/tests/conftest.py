"""
Test Fixtures for School Diary

共通フィクスチャを定義します。各テストで再利用可能なオブジェクトを提供します。

Fixture Pyramid:
- Level 1: 基本オブジェクト（user, classroom）
- Level 2: 関係オブジェクト（diary_entry, teacher_note）
- Level 3: 複雑なシナリオ（setup_inbox_scenario）
"""

from datetime import date
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DiaryEntry

User = get_user_model()


# =============================================================================
# Level 1: 基本オブジェクト
# =============================================================================


@pytest.fixture
def classroom(db):
    """テスト用クラスルーム（1年A組、2025年度）"""
    return ClassRoom.objects.create(
        class_name="A",
        grade=1,
        academic_year=2025,
    )


@pytest.fixture
def student_user(db, classroom):
    """
    生徒ユーザー（STU-001〜004で使用）

    - username: student@test.com
    - password: testpass123
    - role: student
    - classroom: 1年A組
    """
    user = User.objects.create_user(
        username="student@test.com",
        email="student@test.com",
        password="testpass123",
        first_name="太郎",
        last_name="生徒",
    )
    user.profile.role = "student"
    user.profile.save()
    classroom.students.add(user)
    return user


@pytest.fixture
def teacher_user(db, classroom):
    """
    担任ユーザー（TEA-001〜003で使用）

    - username: teacher@test.com
    - password: testpass123
    - role: teacher
    - homeroom_teacher: 1年A組
    """
    user = User.objects.create_user(
        username="teacher@test.com",
        email="teacher@test.com",
        password="testpass123",
        first_name="花子",
        last_name="先生",
    )
    user.profile.role = "teacher"
    user.profile.save()
    classroom.homeroom_teacher = user
    classroom.save()
    return user


@pytest.fixture
def grade_leader_user(db):
    """
    学年主任ユーザー（GRD-001で使用）

    - username: grade_leader@test.com
    - password: testpass123
    - role: grade_leader
    - managed_grade: 1
    """
    user = User.objects.create_user(
        username="grade_leader@test.com",
        email="grade_leader@test.com",
        password="testpass123",
        first_name="次郎",
        last_name="学年主任",
    )
    user.profile.role = "grade_leader"
    user.profile.managed_grade = 1
    user.profile.save()
    return user


@pytest.fixture
def school_leader_user(db):
    """
    校長ユーザー（SCH-001で使用）

    - username: school_leader@test.com
    - password: testpass123
    - role: school_leader
    """
    user = User.objects.create_user(
        username="school_leader@test.com",
        email="school_leader@test.com",
        password="testpass123",
        first_name="三郎",
        last_name="校長",
    )
    user.profile.role = "school_leader"
    user.profile.save()
    return user


@pytest.fixture
def superuser(db):
    """
    システム管理者（ADM-001で使用）

    - username: admin@test.com
    - password: testpass123
    - is_superuser: True
    """
    return User.objects.create_superuser(
        username="admin@test.com",
        email="admin@test.com",
        password="testpass123",
    )


# =============================================================================
# Level 2: 関係オブジェクト
# =============================================================================


@pytest.fixture
def today():
    """今日の日付"""
    return timezone.now().date()


@pytest.fixture
def yesterday():
    """昨日の日付（一日一件制約テスト用）"""
    return timezone.now().date() - timedelta(days=1)


@pytest.fixture
def diary_entry(db, student_user, yesterday):
    """
    テスト用連絡帳エントリー（昨日の日付）

    - student: student_user
    - entry_date: yesterday
    - health_condition: 4
    - mental_condition: 4
    - reflection: テストエントリー
    """
    return DiaryEntry.objects.create(
        student=student_user,
        entry_date=yesterday,
        health_condition=4,
        mental_condition=4,
        reflection="テストエントリー",
    )


@pytest.fixture
def unread_diary_entry(db, student_user, today):
    """
    未読の連絡帳エントリー（今日の日付、担任用テスト用）

    - is_read: False
    - entry_date: today
    """
    return DiaryEntry.objects.create(
        student=student_user,
        entry_date=today,
        health_condition=4,
        mental_condition=4,
        reflection="未読エントリー",
        is_read=False,
    )


# =============================================================================
# Level 3: テストクライアント
# =============================================================================


@pytest.fixture
def client():
    """Djangoテストクライアント"""
    return Client()


@pytest.fixture
def authenticated_student_client(client, student_user):
    """ログイン済み生徒クライアント（STU-001〜004で使用）"""
    client.force_login(student_user)
    return client


@pytest.fixture
def authenticated_teacher_client(client, teacher_user):
    """ログイン済み担任クライアント（TEA-001〜003で使用）"""
    client.force_login(teacher_user)
    return client


@pytest.fixture
def authenticated_grade_leader_client(client, grade_leader_user):
    """ログイン済み学年主任クライアント（GRD-001で使用）"""
    client.force_login(grade_leader_user)
    return client


# =============================================================================
# Level 4: 追加オブジェクト（Priority 2用）
# =============================================================================


@pytest.fixture
def teacher_note(db, teacher_user, student_user):
    """
    担任メモ（個人用、TEA-ACT-003〜005で使用）

    - teacher: teacher_user
    - student: student_user
    - note: テストメモ
    - is_shared: False（個人メモ）
    """
    from school_diary.diary.models import TeacherNote

    return TeacherNote.objects.create(
        teacher=teacher_user,
        student=student_user,
        note="テストメモ：家庭環境良好、保護者協力的",
        is_shared=False,
    )


@pytest.fixture
def shared_teacher_note(db, teacher_user, student_user, classroom):
    """
    学年共有メモ（TEA-ACT-006で使用）

    - teacher: teacher_user
    - student: student_user
    - note: 学年共有メモ
    - is_shared: True（学年全体で共有）
    """
    from school_diary.diary.models import TeacherNote

    return TeacherNote.objects.create(
        teacher=teacher_user,
        student=student_user,
        note="学年共有メモ：要配慮事項あり（アレルギー：卵、乳製品）",
        is_shared=True,
    )

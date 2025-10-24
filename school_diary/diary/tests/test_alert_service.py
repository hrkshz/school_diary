"""Tests for alert_service module (Inbox Pattern backend)

TDD Implementation:
- Red: Write failing tests first
- Green: Implement minimal code to pass
- Refactor: Optimize for N+1 problem
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from school_diary.diary import alert_service
from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DiaryEntry
from school_diary.diary.utils import get_previous_school_day

User = get_user_model()


@pytest.fixture
def setup_classroom(db):
    """テスト用のクラスルームと生徒を作成"""
    # クラスルーム作成
    classroom = ClassRoom.objects.create(
        class_name="A",
        grade=1,
        academic_year=2025,
    )

    # 担任作成
    teacher = User.objects.create_user(
        username="teacher@example.com",
        email="teacher@example.com",
        password="password123",
        first_name="太郎",
        last_name="先生",
    )
    teacher.profile.role = "teacher"
    teacher.profile.save()
    classroom.homeroom_teacher = teacher
    classroom.save()

    # 生徒3名作成
    students = []
    for i in range(3):
        student = User.objects.create_user(
            username=f"student{i + 1}@example.com",
            email=f"student{i + 1}@example.com",
            password="password123",
            first_name=f"生徒{i + 1}",
            last_name="テスト",
        )
        student.profile.role = "student"
        student.profile.save()
        classroom.students.add(student)
        students.append(student)

    return {
        "classroom": classroom,
        "teacher": teacher,
        "students": students,
    }


@pytest.mark.django_db
class TestClassifyStudents:
    """classify_students() のテスト（3段階分類）"""

    def test_classify_important_mental_star_1(self, setup_classroom):
        """メンタル★1の生徒はimportantに分類される"""
        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # メンタル★1のエントリー作成
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=1,  # ★1 = Important
            reflection="つらい",
        )

        result = alert_service.classify_students(classroom)

        assert student in result["important"]
        assert student not in result["needs_attention"]
        assert student not in result["not_submitted"]
        assert student not in result["unread"]
        assert student not in result["no_reaction"]

    def test_classify_completed(self, setup_classroom):
        """既読・反応済みの生徒はcompletedに分類される"""
        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # 健康なエントリー作成（既読・反応済み）
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=5,  # ★★★★★
            mental_condition=5,  # ★★★★★
            reflection="元気です",
            is_read=True,  # 既読
            public_reaction="承知しました",  # 反応済み
        )

        result = alert_service.classify_students(classroom)

        # completedは(student, date)のタプルのリスト
        completed_students = [s for s, d in result["completed"]]
        assert student in completed_students
        assert student not in result["important"]
        assert student not in result["needs_attention"]
        assert student not in result["not_submitted"]
        assert student not in result["unread"]
        assert student not in result["no_reaction"]

    def test_classify_not_submitted(self, setup_classroom):
        """昨日未提出の生徒はnot_submittedに分類される"""
        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        today = timezone.now().date()
        yesterday = get_previous_school_day(today)

        # 前々登校日のエントリーのみ（昨日は未提出）
        DiaryEntry.objects.create(
            student=student,
            entry_date=get_previous_school_day(yesterday),
            health_condition=4,
            mental_condition=4,
            reflection="元気",
        )

        result = alert_service.classify_students(classroom)

        # 昨日未提出 = not_submitted
        assert student in result["not_submitted"]
        assert student not in result["important"]
        assert student not in result["needs_attention"]
        assert student not in result["unread"]
        assert student not in result["no_reaction"]

    def test_classify_unread(self, setup_classroom):
        """未読の生徒はunreadに分類される"""
        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # 健康だが未読のエントリー
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=5,  # ★★★★★（健康）
            mental_condition=5,  # ★★★★★（良好）
            reflection="元気です",
            is_read=False,  # 未読
        )

        result = alert_service.classify_students(classroom)

        # 未読 = unread
        assert student in result["unread"]
        assert student not in result["important"]
        assert student not in result["needs_attention"]
        assert student not in result["not_submitted"]
        assert student not in result["no_reaction"]

    def test_classify_no_reaction(self, setup_classroom):
        """反応未選択の生徒はno_reactionに分類される"""
        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # 既読だが反応未選択のエントリー
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=5,  # ★★★★★（健康）
            mental_condition=5,  # ★★★★★（良好）
            reflection="元気です",
            is_read=True,  # 既読
            public_reaction=None,  # 反応未選択
        )

        result = alert_service.classify_students(classroom)

        # 反応未選択 = no_reaction
        assert student in result["no_reaction"]
        assert student not in result["important"]
        assert student not in result["needs_attention"]
        assert student not in result["not_submitted"]
        assert student not in result["unread"]

    def test_classify_multiple_students(self, setup_classroom):
        """複数の生徒が正しく分類される（6カテゴリ）"""
        classroom = setup_classroom["classroom"]
        students = setup_classroom["students"]
        today = timezone.now().date()

        # 生徒1: Important（メンタル★1）
        DiaryEntry.objects.create(
            student=students[0],
            entry_date=today,
            health_condition=4,
            mental_condition=1,
            reflection="つらい",
        )

        # 生徒2: Unread（未読）
        DiaryEntry.objects.create(
            student=students[1],
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="元気です",
            is_read=False,  # 未読
        )

        # 生徒3: Completed（健康、既読・反応済み）
        DiaryEntry.objects.create(
            student=students[2],
            entry_date=today,
            health_condition=5,
            mental_condition=5,
            reflection="元気",
            is_read=True,  # 既読
            public_reaction="承知しました",  # 反応済み
        )

        result = alert_service.classify_students(classroom)

        assert students[0] in result["important"]
        assert students[1] in result["unread"]
        completed_students = [s for s, d in result["completed"]]
        assert students[2] in completed_students

    def test_no_n_plus_one_problem(self, setup_classroom, django_assert_num_queries):
        """N+1問題が発生しないことを確認（クエリ数=2）"""
        classroom = setup_classroom["classroom"]
        students = setup_classroom["students"]
        today = timezone.now().date()

        # 全生徒にエントリー作成
        for student in students:
            DiaryEntry.objects.create(
                student=student,
                entry_date=today,
                health_condition=4,
                mental_condition=3,
                reflection="普通",
            )

        # クエリ数を確認（生徒数に関わらず2クエリ）
        # Query 1: DiaryEntry一括取得（select_related('student')）
        # Query 2: classroom.students.all()
        with django_assert_num_queries(2):
            alert_service.classify_students(classroom)


@pytest.mark.django_db
class TestCheckConsecutiveDecline:
    """_check_consecutive_decline() のテスト（3日連続低下検出）"""

    def test_check_consecutive_decline_true(self, setup_classroom):
        """3日連続低下（5→4→3）はTrueを返す"""
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # 3日分のエントリー作成（5→4→3）
        entries = []
        for i, mental in enumerate([5, 4, 3]):
            date = today - timedelta(days=2 - i)
            entry = DiaryEntry.objects.create(
                student=student,
                entry_date=date,
                health_condition=4,
                mental_condition=mental,
                reflection=f"Day {i}",
            )
            entries.append(entry)

        # 最新順にソート（alert_serviceのentries_by_studentと同じ形式）
        entries_sorted = sorted(entries, key=lambda e: e.entry_date, reverse=True)

        result = alert_service._check_consecutive_decline(entries_sorted)
        assert result is True

    def test_check_consecutive_decline_false_flat(self, setup_classroom):
        """横ばい（4→4→4）はFalseを返す"""
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        entries = []
        for i in range(3):
            date = today - timedelta(days=2 - i)
            entry = DiaryEntry.objects.create(
                student=student,
                entry_date=date,
                health_condition=4,
                mental_condition=4,  # 横ばい
                reflection=f"Day {i}",
            )
            entries.append(entry)

        entries_sorted = sorted(entries, key=lambda e: e.entry_date, reverse=True)
        result = alert_service._check_consecutive_decline(entries_sorted)
        assert result is False

    def test_check_consecutive_decline_false_recovery(self, setup_classroom):
        """回復傾向（2→3→4）はFalseを返す"""
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        entries = []
        for i, mental in enumerate([2, 3, 4]):
            date = today - timedelta(days=2 - i)
            entry = DiaryEntry.objects.create(
                student=student,
                entry_date=date,
                health_condition=4,
                mental_condition=mental,  # 回復
                reflection=f"Day {i}",
            )
            entries.append(entry)

        entries_sorted = sorted(entries, key=lambda e: e.entry_date, reverse=True)
        result = alert_service._check_consecutive_decline(entries_sorted)
        assert result is False

    def test_check_consecutive_decline_false_v_shape(self, setup_classroom):
        """V字回復（5→2→5）はFalseを返す"""
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        entries = []
        for i, mental in enumerate([5, 2, 5]):
            date = today - timedelta(days=2 - i)
            entry = DiaryEntry.objects.create(
                student=student,
                entry_date=date,
                health_condition=4,
                mental_condition=mental,  # V字回復
                reflection=f"Day {i}",
            )
            entries.append(entry)

        entries_sorted = sorted(entries, key=lambda e: e.entry_date, reverse=True)
        result = alert_service._check_consecutive_decline(entries_sorted)
        assert result is False

    def test_check_consecutive_decline_insufficient_data(self, setup_classroom):
        """データ不足（2件のみ）はFalseを返す"""
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        entries = []
        for i in range(2):  # 2件のみ
            date = today - timedelta(days=1 - i)
            entry = DiaryEntry.objects.create(
                student=student,
                entry_date=date,
                health_condition=4,
                mental_condition=4,
                reflection=f"Day {i}",
            )
            entries.append(entry)

        entries_sorted = sorted(entries, key=lambda e: e.entry_date, reverse=True)
        result = alert_service._check_consecutive_decline(entries_sorted)
        assert result is False

    def test_classify_needs_attention_3day_decline(self, setup_classroom):
        """3日連続低下の生徒はneeds_attentionに分類される"""
        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # 3日連続低下（5→4→3）
        for i, mental in enumerate([5, 4, 3]):
            date = today - timedelta(days=2 - i)
            DiaryEntry.objects.create(
                student=student,
                entry_date=date,
                health_condition=4,
                mental_condition=mental,
                reflection=f"Day {i}",
            )

        result = alert_service.classify_students(classroom)

        assert student in result["needs_attention"]
        assert student not in result["important"]

    def test_classify_priority_important_over_attention(self, setup_classroom):
        """メンタル★1 + 3日連続低下の場合、importantが優先される"""
        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # 3日連続低下 + 最新日がメンタル★1
        for i, mental in enumerate([5, 2, 1]):  # 5→2→1
            date = today - timedelta(days=2 - i)
            DiaryEntry.objects.create(
                student=student,
                entry_date=date,
                health_condition=4,
                mental_condition=mental,
                reflection=f"Day {i}",
            )

        result = alert_service.classify_students(classroom)

        # メンタル★1が優先される（排他的分類）
        assert student in result["important"]
        assert student not in result["needs_attention"]


@pytest.mark.django_db
class TestFormatInlineHistory:
    """format_inline_history() のテスト（直近3日の履歴表示）"""

    def test_format_inline_history_3_days(self, setup_classroom):
        """直近3日の履歴が正しくフォーマットされる"""
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # 3日分のエントリー作成
        entries = []
        for i in range(3):
            date = today - timedelta(days=2 - i)
            entry = DiaryEntry.objects.create(
                student=student,
                entry_date=date,
                health_condition=4 - i,  # 4, 3, 2（低下）
                mental_condition=4 - i,
                reflection=f"Day {i}",
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
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        entry = DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=3,
            reflection="今日は元気です。",
        )

        result = alert_service.get_snippet(entry)

        assert result == "今日は元気です。"

    def test_get_snippet_long_text(self, setup_classroom):
        """50文字を超えるテキストは省略される"""
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        long_text = "今日は部活で先輩に怒られてしまいました。理由がよく分からないのでとても悲しいです。明日はもっと頑張りたいです。"
        entry = DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=3,
            reflection=long_text,
        )

        result = alert_service.get_snippet(entry)

        assert len(result) <= 53  # 50文字 + "..."
        assert result.endswith("...")
        assert result.startswith("今日は部活で")


@pytest.mark.django_db
class TestClassifyStudentsWeekendHandling:
    """土日を考慮した未提出判定のテスト（TDD: Red→Green→Refactor）"""

    def setup_method(self):
        """テストデータ準備"""
        # 担任を作成
        self.teacher = User.objects.create_user(
            username="teacher_weekend",
            email="teacher_weekend@example.com",
            password="password123",
            first_name="太郎",
            last_name="先生",
        )

        # クラスを作成
        self.classroom = ClassRoom.objects.create(
            class_name="A",
            grade=1,
            academic_year=2025,
            homeroom_teacher=self.teacher,
        )

        # 生徒を作成
        self.student_a = User.objects.create_user(
            username="student_a_weekend",
            email="student_a@example.com",
            password="password123",
            first_name="花子",
            last_name="生徒A",
        )
        self.student_a.classes.add(self.classroom)

        self.student_b = User.objects.create_user(
            username="student_b_weekend",
            email="student_b@example.com",
            password="password123",
            first_name="次郎",
            last_name="生徒B",
        )
        self.student_b.classes.add(self.classroom)

    def test_monday_with_friday_entry_should_be_completed(self):
        """月曜日: 金曜日に提出した生徒は「対応済み」に分類される"""
        from datetime import date
        from datetime import datetime
        from unittest.mock import patch

        # 月曜日（2025-10-20）をモック
        mock_datetime = datetime(2025, 10, 20, 9, 0, 0)

        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = mock_datetime

            # 金曜日（2025-10-17）にエントリー作成、既読+反応済み
            DiaryEntry.objects.create(
                student=self.student_a,
                entry_date=date(2025, 10, 17),  # 金曜日
                reflection="金曜日の連絡帳",
                health_condition=4,
                mental_condition=4,
                is_read=True,
                read_by=self.teacher,
                public_reaction="understood",
            )

            # 分類実行
            result = alert_service.classify_students(self.classroom)

            # 生徒Aは「対応済み」に分類される（金曜日=前登校日）
            completed_ids = [s.id for s, d in result["completed"]]
            assert self.student_a.id in completed_ids, "金曜日に提出した生徒Aは「対応済み」に分類されるべき"

            # 生徒Aは「未提出」に分類されない
            assert self.student_a not in result["not_submitted"], "金曜日に提出した生徒Aは「未提出」に分類されないべき"

    def test_monday_without_friday_entry_should_be_not_submitted(self):
        """月曜日: 金曜日に提出していない生徒は「未提出」に分類される"""
        from datetime import date
        from datetime import datetime
        from unittest.mock import patch

        # 月曜日（2025-10-20）をモック
        mock_datetime = datetime(2025, 10, 20, 9, 0, 0)

        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = mock_datetime

            # 木曜日（2025-10-16）にエントリー作成（金曜日は未提出）
            DiaryEntry.objects.create(
                student=self.student_b,
                entry_date=date(2025, 10, 16),  # 木曜日（金曜日より古い）
                reflection="木曜日の連絡帳",
                health_condition=4,
                mental_condition=4,
                is_read=True,
                read_by=self.teacher,
                public_reaction="understood",
            )

            # 分類実行
            result = alert_service.classify_students(self.classroom)

            # 生徒Bは「未提出」に分類される（前登校日=金曜日に提出なし）
            assert self.student_b in result["not_submitted"], "金曜日に提出していない生徒Bは「未提出」に分類されるべき"

            # 生徒Bは「対応済み」に分類されない
            completed_ids = [s.id for s, d in result["completed"]]
            assert self.student_b.id not in completed_ids, "金曜日に提出していない生徒Bは「対応済み」に分類されないべき"

    def test_monday_integrated_multiple_students(self):
        """月曜日: 複数生徒の分類が正しく動作する統合テスト"""
        from datetime import date
        from datetime import datetime
        from unittest.mock import patch

        # 月曜日（2025-10-20）をモック
        mock_datetime = datetime(2025, 10, 20, 9, 0, 0)

        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value = mock_datetime

            # 生徒A: 金曜日に提出（対応済み）
            DiaryEntry.objects.create(
                student=self.student_a,
                entry_date=date(2025, 10, 17),  # 金曜日
                reflection="金曜日の連絡帳",
                health_condition=4,
                mental_condition=4,
                is_read=True,
                read_by=self.teacher,
                public_reaction="understood",
            )

            # 生徒B: 木曜日に提出（未提出扱い）
            DiaryEntry.objects.create(
                student=self.student_b,
                entry_date=date(2025, 10, 16),  # 木曜日
                reflection="木曜日の連絡帳",
                health_condition=4,
                mental_condition=4,
                is_read=True,
                read_by=self.teacher,
                public_reaction="understood",
            )

            # 分類実行
            result = alert_service.classify_students(self.classroom)

            # 生徒Aは「対応済み」
            completed_ids = [s.id for s, d in result["completed"]]
            assert self.student_a.id in completed_ids, "生徒Aは対応済みに分類されるべき"

            # 生徒Bは「未提出」
            assert self.student_b in result["not_submitted"], "生徒Bは未提出に分類されるべき"

            # カウント確認（「未対応」として表示される人数）
            needs_response_count = len(result["not_submitted"]) + len(result["unread"]) + len(result["no_reaction"])
            assert needs_response_count >= 1, "「未対応」が1名以上いるべき"

    def test_classify_needs_action_with_internal_action_pending(self, setup_classroom):
        """internal_actionが設定されaction_status=PENDINGの生徒はneeds_actionに分類される"""
        from school_diary.diary.models import ActionStatus
        from school_diary.diary.models import InternalAction

        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # internal_action設定済み、action_status=PENDINGのエントリー作成
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=3,
            reflection="テスト",
            internal_action=InternalAction.NEEDS_FOLLOW_UP,
            action_status=ActionStatus.PENDING,
        )

        result = alert_service.classify_students(classroom)

        # needs_actionに分類されることを確認
        assert len(result["needs_action"]) == 1
        student_in_needs_action, entry_in_needs_action = result["needs_action"][0]
        assert student_in_needs_action.id == student.id
        assert entry_in_needs_action.internal_action == InternalAction.NEEDS_FOLLOW_UP

        # 他のカテゴリに分類されていないことを確認
        assert student not in result["important"]
        assert student not in result["needs_attention"]
        assert student not in result["not_submitted"]
        assert student not in result["unread"]
        assert student not in result["no_reaction"]

    def test_classify_needs_action_with_internal_action_in_progress(self, setup_classroom):
        """internal_actionが設定されaction_status=IN_PROGRESSの生徒はneeds_actionに分類される"""
        from school_diary.diary.models import ActionStatus
        from school_diary.diary.models import InternalAction

        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # internal_action設定済み、action_status=IN_PROGRESSのエントリー作成
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=3,
            reflection="テスト",
            internal_action=InternalAction.URGENT,
            action_status=ActionStatus.IN_PROGRESS,
        )

        result = alert_service.classify_students(classroom)

        # needs_actionに分類されることを確認
        assert len(result["needs_action"]) == 1
        student_in_needs_action, entry_in_needs_action = result["needs_action"][0]
        assert student_in_needs_action.id == student.id
        assert entry_in_needs_action.internal_action == InternalAction.URGENT

    def test_classify_not_needs_action_when_completed(self, setup_classroom):
        """internal_actionが設定されていてもaction_status=COMPLETEDならneeds_actionに分類されない"""
        from school_diary.diary.models import ActionStatus
        from school_diary.diary.models import InternalAction
        from school_diary.diary.models import PublicReaction

        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        teacher = setup_classroom["teacher"]
        today = timezone.now().date()

        # internal_action設定済み、action_status=COMPLETEDのエントリー作成
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=3,
            reflection="テスト",
            internal_action=InternalAction.NEEDS_FOLLOW_UP,
            action_status=ActionStatus.COMPLETED,
            is_read=True,
            read_by=teacher,
            read_at=timezone.now(),
            public_reaction=PublicReaction.THUMBS_UP,
        )

        result = alert_service.classify_students(classroom)

        # needs_actionに分類されないことを確認
        assert len(result["needs_action"]) == 0

        # completedに分類されることを確認
        completed_ids = [s.id for s, d in result["completed"]]
        assert student.id in completed_ids

    def test_classify_needs_action_priority_over_unread(self, setup_classroom):
        """internal_action設定済みの生徒は、未読でもneeds_actionに優先的に分類される"""
        from school_diary.diary.models import ActionStatus
        from school_diary.diary.models import InternalAction

        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # internal_action設定済み、未読のエントリー作成
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=3,
            reflection="テスト",
            internal_action=InternalAction.PARENT_CONTACTED,
            action_status=ActionStatus.PENDING,
            is_read=False,  # 未読
        )

        result = alert_service.classify_students(classroom)

        # needs_actionに分類されることを確認（unreadより優先）
        assert len(result["needs_action"]) == 1
        assert len(result["unread"]) == 0


@pytest.mark.django_db
class TestTriageSystem:
    """トリアージシステムのテスト（action_status=PENDINGフィルタリング）"""

    def test_important_excludes_triaged_entries(self, setup_classroom):
        """P0（重要）: トリアージ済み（action_status != PENDING）のメンタル★1は除外される"""
        from school_diary.diary.models import ActionStatus

        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        teacher = setup_classroom["teacher"]
        today = timezone.now().date()

        # メンタル★1だが、action_status=NOT_REQUIRED（トリアージ済み）
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=1,  # ★1
            reflection="つらい",
            action_status=ActionStatus.NOT_REQUIRED,  # トリアージ済み
            is_read=True,
            read_by=teacher,
        )

        result = alert_service.classify_students(classroom)

        # importantに分類されないことを確認
        assert student not in result["important"]
        # no_reactionに分類される（既読だが反応未選択）
        assert student in result["no_reaction"]

    def test_important_includes_untriaged_mental_1(self, setup_classroom):
        """P0（重要）: action_status=PENDINGのメンタル★1は分類される"""
        from school_diary.diary.models import ActionStatus

        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # メンタル★1、action_status=PENDING（未トリアージ）
        DiaryEntry.objects.create(
            student=student,
            entry_date=today,
            health_condition=4,
            mental_condition=1,  # ★1
            reflection="つらい",
            action_status=ActionStatus.PENDING,  # 未トリアージ
        )

        result = alert_service.classify_students(classroom)

        # importantに分類されることを確認
        assert student in result["important"]

    def test_needs_attention_excludes_triaged_entries(self, setup_classroom):
        """P1（要注意）: トリアージ済み（action_status != PENDING）の3日連続低下は除外される"""
        from school_diary.diary.models import ActionStatus

        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        teacher = setup_classroom["teacher"]
        today = timezone.now().date()

        # 3日連続低下（5→4→3）だが、最新がaction_status=NOT_REQUIRED
        for i, mental in enumerate([5, 4, 3]):
            date = today - timedelta(days=2 - i)
            action_status = ActionStatus.NOT_REQUIRED if i == 2 else ActionStatus.PENDING
            DiaryEntry.objects.create(
                student=student,
                entry_date=date,
                health_condition=4,
                mental_condition=mental,
                reflection=f"Day {i}",
                action_status=action_status,  # 最新日のみトリアージ済み
                is_read=(i == 2),
                read_by=teacher if i == 2 else None,
            )

        result = alert_service.classify_students(classroom)

        # needs_attentionに分類されないことを確認
        assert student not in result["needs_attention"]
        # no_reactionに分類される（既読だが反応未選択）
        assert student in result["no_reaction"]

    def test_needs_attention_includes_untriaged_decline(self, setup_classroom):
        """P1（要注意）: action_status=PENDINGの3日連続低下は分類される"""
        from school_diary.diary.models import ActionStatus

        classroom = setup_classroom["classroom"]
        student = setup_classroom["students"][0]
        today = timezone.now().date()

        # 3日連続低下（5→4→3）、action_status=PENDING
        for i, mental in enumerate([5, 4, 3]):
            date = today - timedelta(days=2 - i)
            DiaryEntry.objects.create(
                student=student,
                entry_date=date,
                health_condition=4,
                mental_condition=mental,
                reflection=f"Day {i}",
                action_status=ActionStatus.PENDING,  # 未トリアージ
            )

        result = alert_service.classify_students(classroom)

        # needs_attentionに分類されることを確認
        assert student in result["needs_attention"]

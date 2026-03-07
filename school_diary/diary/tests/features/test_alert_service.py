"""
Alert Service Unit Tests

このモジュールは内部ロジックの正確性をテストします（Unit Tests）。
統合テスト（Integration Tests）とは粒度が異なりますが、
両方を features/ ディレクトリで管理することで、保守性を向上させています。

テスト対象ロジック:
- classify_students(): 5段階分類アルゴリズム
- _check_consecutive_decline(): 3日連続メンタル低下判定
- _is_critical(): メンタル★1検知
- _needs_action(): 要対応タスク判定
- format_inline_history(): 履歴フォーマット
- get_snippet(): スニペット生成

Priority: P0（クリティカル）
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from school_diary.diary.services.alert_service import _check_consecutive_decline
from school_diary.diary.services.alert_service import _is_critical
from school_diary.diary.services.alert_service import _needs_action
from school_diary.diary.services.alert_service import classify_students
from school_diary.diary.services.alert_service import format_inline_history
from school_diary.diary.services.alert_service import get_snippet
from school_diary.diary.models import ActionStatus
from school_diary.diary.models import DiaryEntry


@pytest.mark.django_db
class TestClassifyStudentsImportant:
    """classify_students()のP0（重要）分類テスト"""

    def test_classify_mental_1_as_important(
        self,
        classroom,
        student_user,
        today,
    ):
        """
        Given: メンタル★1の連絡帳エントリー
        When: classify_students()を呼ぶ
        Then: importantに分類される
        """
        # Arrange
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=1,  # ★1
            reflection="つらい",
        )

        # Act
        result = classify_students(classroom)

        # Assert
        assert student_user in result["important"]


@pytest.mark.django_db
class TestClassifyStudentsNeedsAttention:
    """classify_students()のP1（要注意）分類テスト"""

    def test_classify_consecutive_decline_as_needs_attention(
        self,
        classroom,
        student_user,
        today,
    ):
        """
        Given: 3日連続メンタル低下（5→4→3）
        When: classify_students()を呼ぶ
        Then: needs_attentionに分類される
        """
        # Arrange: 3日連続低下
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=today - timedelta(days=2),
            health_condition=4,
            mental_condition=5,  # day1
            reflection="元気",
        )
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=today - timedelta(days=1),
            health_condition=4,
            mental_condition=4,  # day2
            reflection="まあまあ",
        )
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=3,  # day3（低下）
            reflection="ちょっと疲れた",
        )

        # Act
        result = classify_students(classroom)

        # Assert
        assert student_user in result["needs_attention"]


@pytest.mark.django_db
class TestClassifyStudentsNeedsAction:
    """classify_students()のP1.5（要対応タスク）分類テスト"""

    def test_classify_with_internal_action_as_needs_action(
        self,
        classroom,
        student_user,
        today,
    ):
        """
        Given: internal_action設定済み、action_status=IN_PROGRESS
        When: classify_students()を呼ぶ
        Then: needs_actionに分類される
        """
        # Arrange
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            internal_action="parent_contact",
            action_status=ActionStatus.IN_PROGRESS,
        )

        # Act
        result = classify_students(classroom)

        # Assert
        assert (student_user, entry) in result["needs_action"]


@pytest.mark.django_db
class TestClassifyStudentsNotSubmitted:
    """classify_students()のP2-1（未提出）分類テスト"""

    def test_classify_no_entry_as_not_submitted(
        self,
        classroom,
        student_user,
    ):
        """
        Given: 連絡帳エントリーなし
        When: classify_students()を呼ぶ
        Then: not_submittedに分類される
        """
        # Arrange: 連絡帳なし

        # Act
        result = classify_students(classroom)

        # Assert
        assert student_user in result["not_submitted"]


@pytest.mark.django_db
class TestClassifyStudentsUnread:
    """classify_students()のP2-2（未読）分類テスト"""

    def test_classify_unread_entry_as_unread(
        self,
        classroom,
        student_user,
        today,
    ):
        """
        Given: 未読の連絡帳エントリー
        When: classify_students()を呼ぶ
        Then: unreadに分類される
        """
        # Arrange
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            is_read=False,
        )

        # Act
        result = classify_students(classroom)

        # Assert
        assert student_user in result["unread"]


@pytest.mark.django_db
class TestClassifyStudentsCompleted:
    """classify_students()のP3（対応済み）分類テスト"""

    def test_classify_read_entry_as_completed(
        self,
        classroom,
        student_user,
        teacher_user,
        yesterday,
    ):
        """
        Given: 既読の連絡帳エントリー（前登校日以降）
        When: classify_students()を呼ぶ
        Then: completedに分類される
        """
        # Arrange
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
        )
        entry.mark_as_read(teacher_user)

        # Act
        result = classify_students(classroom)

        # Assert
        assert (student_user, yesterday) in result["completed"]


@pytest.mark.django_db
class TestCheckConsecutiveDecline:
    """_check_consecutive_decline()のテスト"""

    def test_consecutive_decline_3days_returns_true(
        self,
        student_user,
        today,
    ):
        """
        Given: 3日連続メンタル低下（5→4→3）
        When: _check_consecutive_decline()を呼ぶ
        Then: True
        """
        # Arrange
        entries = [
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today - timedelta(days=2),
                health_condition=4,
                mental_condition=5,
                reflection="day1",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today - timedelta(days=1),
                health_condition=4,
                mental_condition=4,
                reflection="day2",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today,
                health_condition=4,
                mental_condition=3,
                reflection="day3",
            ),
        ]

        # Act
        result = _check_consecutive_decline(entries)

        # Assert
        assert result

    def test_consecutive_decline_flat_returns_false(
        self,
        student_user,
        today,
    ):
        """
        Given: 3日連続で同じメンタル（4→4→4）
        When: _check_consecutive_decline()を呼ぶ
        Then: False（低下していない）
        """
        # Arrange
        entries = [
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today - timedelta(days=2),
                health_condition=4,
                mental_condition=4,
                reflection="day1",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today - timedelta(days=1),
                health_condition=4,
                mental_condition=4,
                reflection="day2",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today,
                health_condition=4,
                mental_condition=4,
                reflection="day3",
            ),
        ]

        # Act
        result = _check_consecutive_decline(entries)

        # Assert
        assert not result

    def test_consecutive_decline_less_than_3_returns_false(
        self,
        student_user,
        today,
    ):
        """
        Given: 2日分のエントリー
        When: _check_consecutive_decline()を呼ぶ
        Then: False（3日分ない）
        """
        # Arrange
        entries = [
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today - timedelta(days=1),
                health_condition=4,
                mental_condition=5,
                reflection="day1",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today,
                health_condition=4,
                mental_condition=4,
                reflection="day2",
            ),
        ]

        # Act
        result = _check_consecutive_decline(entries)

        # Assert
        assert not result


@pytest.mark.django_db
class TestIsCritical:
    """_is_critical()のテスト"""

    def test_is_critical_mental_1_pending_returns_true(
        self,
        student_user,
        today,
    ):
        """
        Given: メンタル★1、action_status=PENDING
        When: _is_critical()を呼ぶ
        Then: True
        """
        # Arrange
        from school_diary.diary.utils import get_previous_school_day

        yesterday = get_previous_school_day(today)

        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=1,
            reflection="つらい",
            action_status=ActionStatus.PENDING,
        )

        # Act
        result = _is_critical(entry, [entry], today, yesterday)

        # Assert
        assert result

    def test_is_critical_mental_1_completed_returns_false(
        self,
        student_user,
        teacher_user,
        today,
    ):
        """
        Given: メンタル★1、action_status=COMPLETED
        When: _is_critical()を呼ぶ
        Then: False（既にトリアージ済み）
        """
        # Arrange
        from school_diary.diary.utils import get_previous_school_day

        yesterday = get_previous_school_day(today)

        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=1,
            reflection="つらい",
            action_status=ActionStatus.COMPLETED,
            action_completed_by=teacher_user,
            action_completed_at=timezone.now(),
        )

        # Act
        result = _is_critical(entry, [entry], today, yesterday)

        # Assert
        assert not result


@pytest.mark.django_db
class TestNeedsAction:
    """_needs_action()のテスト"""

    def test_needs_action_with_internal_action_pending_returns_true(
        self,
        student_user,
        today,
    ):
        """
        Given: internal_action設定済み、action_status=PENDING
        When: _needs_action()を呼ぶ
        Then: True
        """
        # Arrange
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            internal_action="parent_contact",
            action_status=ActionStatus.PENDING,
        )

        # Act
        result = _needs_action(entry)

        # Assert
        assert result

    def test_needs_action_without_internal_action_returns_false(
        self,
        student_user,
        today,
    ):
        """
        Given: internal_actionなし
        When: _needs_action()を呼ぶ
        Then: False
        """
        # Arrange
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            internal_action="",
            action_status=ActionStatus.PENDING,
        )

        # Act
        result = _needs_action(entry)

        # Assert
        assert not result

    def test_needs_action_with_internal_action_completed_returns_false(
        self,
        student_user,
        teacher_user,
        today,
    ):
        """
        Given: internal_action設定済み、action_status=COMPLETED
        When: _needs_action()を呼ぶ
        Then: False（対応完了済み）
        """
        # Arrange
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            internal_action="parent_contact",
            action_status=ActionStatus.COMPLETED,
            action_completed_by=teacher_user,
            action_completed_at=timezone.now(),
        )

        # Act
        result = _needs_action(entry)

        # Assert
        assert not result


@pytest.mark.django_db
class TestFormatInlineHistory:
    """format_inline_history()のテスト"""

    def test_format_inline_history_3entries(
        self,
        student_user,
        today,
    ):
        """
        Given: 3日分のエントリー
        When: format_inline_history()を呼ぶ
        Then: "MM/DD(★★★)→MM/DD(★★★★)→MM/DD(★★★★★)" 形式
        """
        # Arrange
        entries = [
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today - timedelta(days=2),
                health_condition=4,
                mental_condition=3,
                reflection="day1",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today - timedelta(days=1),
                health_condition=4,
                mental_condition=4,
                reflection="day2",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today,
                health_condition=4,
                mental_condition=5,
                reflection="day3",
            ),
        ]

        # Act
        result = format_inline_history(entries)

        # Assert
        # 古い順にソート: day1 → day2 → day3
        date1 = (today - timedelta(days=2)).strftime("%m/%d")
        date2 = (today - timedelta(days=1)).strftime("%m/%d")
        date3 = today.strftime("%m/%d")
        expected = f"{date1}(★★★)→{date2}(★★★★)→{date3}(★★★★★)"
        assert result == expected

    def test_format_inline_history_empty_returns_empty_string(self):
        """
        Given: エントリーなし
        When: format_inline_history()を呼ぶ
        Then: 空文字列
        """
        # Act
        result = format_inline_history([])

        # Assert
        assert result == ""


@pytest.mark.django_db
class TestGetSnippet:
    """get_snippet()のテスト"""

    def test_get_snippet_short_text_returns_as_is(
        self,
        student_user,
        today,
    ):
        """
        Given: 短いテキスト（50文字以内）
        When: get_snippet()を呼ぶ
        Then: そのまま返す
        """
        # Arrange
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="短いテキスト",
        )

        # Act
        result = get_snippet(entry)

        # Assert
        assert result == "短いテキスト"

    def test_get_snippet_long_text_truncates_with_ellipsis(
        self,
        student_user,
        today,
    ):
        """
        Given: 長いテキスト（50文字超）
        When: get_snippet()を呼ぶ
        Then: 50文字 + "..." で切り詰める
        """
        # Arrange
        long_text = "あ" * 60  # 60文字
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection=long_text,
        )

        # Act
        result = get_snippet(entry)

        # Assert
        assert len(result) == 53  # 50 + "..."
        assert result.endswith("...")

    def test_get_snippet_none_entry_returns_empty_string(self):
        """
        Given: entry=None
        When: get_snippet()を呼ぶ
        Then: 空文字列
        """
        # Act
        result = get_snippet(None)

        # Assert
        assert result == ""

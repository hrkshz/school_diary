"""
Alert Service Unit Tests

このモジュールは内部ロジックの正確性をテストします（Unit Tests）。
統合テスト（Integration Tests）とは粒度が異なりますが、
両方を features/ ディレクトリで管理することで、保守性を向上させています。

テスト対象ロジック:
- classify_students(): 5段階分類アルゴリズム
- _check_consecutive_decline(): 連続登校日でのmental/health低下判定
- _is_critical() / _find_critical_entry(): mental/health ★1検知
- _needs_action(): 要対応タスク判定
- format_inline_history(): 履歴フォーマット
- get_snippet(): スニペット生成

Priority: P0（クリティカル）
"""

from datetime import timedelta

import pytest
from django.utils import timezone

from school_diary.diary.models import ActionStatus
from school_diary.diary.models import DiaryEntry
from school_diary.diary.services.alert_service import _check_consecutive_decline
from school_diary.diary.services.alert_service import _find_critical_entry
from school_diary.diary.services.alert_service import _is_critical
from school_diary.diary.services.alert_service import _needs_action
from school_diary.diary.services.alert_service import classify_students
from school_diary.diary.services.alert_service import format_inline_history
from school_diary.diary.services.alert_service import get_snippet
from school_diary.diary.utils import get_previous_school_day


def _get_consecutive_school_days(base_date, count=3):
    """テスト用: base_dateから遡って連続登校日をcount日分返す（古い順）"""
    dates = [base_date]
    for _ in range(count - 1):
        dates.append(get_previous_school_day(dates[-1]))
    return list(reversed(dates))  # 古い順


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
        Then: importantに分類される（タプル形式）
        """
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=1,
            reflection="つらい",
        )

        result = classify_students(classroom)

        students_in_important = [s for s, _e in result["important"]]
        assert student_user in students_in_important

    def test_classify_health_1_as_important(
        self,
        classroom,
        student_user,
        today,
    ):
        """
        Given: 体調★1の連絡帳エントリー
        When: classify_students()を呼ぶ
        Then: importantに分類される
        """
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=1,
            mental_condition=4,
            reflection="体調が悪い",
        )

        result = classify_students(classroom)

        students_in_important = [s for s, _e in result["important"]]
        assert student_user in students_in_important

    def test_classify_past_unread_mental_1_as_important(
        self,
        classroom,
        student_user,
        today,
        yesterday,
    ):
        """
        Given: 昨日のメンタル★1（未読）+ 今日のメンタル4
        When: classify_students()を呼ぶ
        Then: 昨日のエントリーでimportantに分類される（見逃し防止）
        """
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=1,
            reflection="昨日つらかった",
            is_read=False,
        )
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="今日は普通",
        )

        result = classify_students(classroom)

        students_in_important = [s for s, _e in result["important"]]
        assert student_user in students_in_important

    def test_classify_resolved_mental_1_not_important(
        self,
        classroom,
        student_user,
        teacher_user,
        today,
    ):
        """
        Given: メンタル★1だが既読＆対応完了
        When: classify_students()を呼ぶ
        Then: importantに分類されない
        """
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=1,
            reflection="つらい",
            is_read=True,
            action_status=ActionStatus.COMPLETED,
            action_completed_by=teacher_user,
            action_completed_at=timezone.now(),
        )

        result = classify_students(classroom)

        students_in_important = [s for s, _e in result["important"]]
        assert student_user not in students_in_important


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
        Given: 連続登校日3日間でメンタル低下（5→4→3）
        When: classify_students()を呼ぶ
        Then: needs_attentionに分類される
        """
        dates = _get_consecutive_school_days(today)
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=dates[0],
            health_condition=4,
            mental_condition=5,
            reflection="元気",
        )
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=dates[1],
            health_condition=4,
            mental_condition=4,
            reflection="まあまあ",
        )
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=dates[2],
            health_condition=4,
            mental_condition=3,
            reflection="ちょっと疲れた",
        )

        result = classify_students(classroom)

        assert student_user in result["needs_attention"]

    def test_small_decline_not_needs_attention(
        self,
        classroom,
        student_user,
        today,
    ):
        """
        Given: 5→5→4（1ポイントしか低下していない）
        When: classify_students()を呼ぶ
        Then: needs_attentionに分類されない
        """
        dates = _get_consecutive_school_days(today)
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=dates[0],
            health_condition=4,
            mental_condition=5,
            reflection="day1",
        )
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=dates[1],
            health_condition=4,
            mental_condition=5,
            reflection="day2",
        )
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=dates[2],
            health_condition=4,
            mental_condition=4,
            reflection="day3",
        )

        result = classify_students(classroom)

        assert student_user not in result["needs_attention"]


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
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            internal_action="parent_contact",
            action_status=ActionStatus.IN_PROGRESS,
        )

        result = classify_students(classroom)

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
        result = classify_students(classroom)

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
        DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            is_read=False,
        )

        result = classify_students(classroom)

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
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
        )
        entry.mark_as_read(teacher_user)

        result = classify_students(classroom)

        assert (student_user, yesterday) in result["completed"]


@pytest.mark.django_db
class TestCheckConsecutiveDecline:
    """_check_consecutive_decline()のテスト"""

    def test_mental_decline_5_4_3_returns_true(
        self,
        student_user,
        today,
    ):
        """
        Given: 連続登校日でメンタル5→4→3
        When: _check_consecutive_decline()を呼ぶ
        Then: True（2ポイント低下、最終値3）
        """
        dates = _get_consecutive_school_days(today)
        entries = [
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[0],
                health_condition=4,
                mental_condition=5,
                reflection="day1",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[1],
                health_condition=4,
                mental_condition=4,
                reflection="day2",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[2],
                health_condition=4,
                mental_condition=3,
                reflection="day3",
            ),
        ]

        result = _check_consecutive_decline(entries)

        assert result

    def test_small_decline_5_5_4_returns_false(
        self,
        student_user,
        today,
    ):
        """
        Given: メンタル5→5→4（1ポイントしか低下していない）
        When: _check_consecutive_decline()を呼ぶ
        Then: False
        """
        dates = _get_consecutive_school_days(today)
        entries = [
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[0],
                health_condition=4,
                mental_condition=5,
                reflection="day1",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[1],
                health_condition=4,
                mental_condition=5,
                reflection="day2",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[2],
                health_condition=4,
                mental_condition=4,
                reflection="day3",
            ),
        ]

        result = _check_consecutive_decline(entries)

        assert not result

    def test_small_decline_5_4_4_returns_false(
        self,
        student_user,
        today,
    ):
        """
        Given: メンタル5→4→4（1ポイントしか低下していない）
        When: _check_consecutive_decline()を呼ぶ
        Then: False
        """
        dates = _get_consecutive_school_days(today)
        entries = [
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[0],
                health_condition=4,
                mental_condition=5,
                reflection="day1",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[1],
                health_condition=4,
                mental_condition=4,
                reflection="day2",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[2],
                health_condition=4,
                mental_condition=4,
                reflection="day3",
            ),
        ]

        result = _check_consecutive_decline(entries)

        assert not result

    def test_decline_ending_above_normal_returns_false(
        self,
        student_user,
        today,
    ):
        """
        Given: メンタル5→5→4（最終値4＝「良い」、3以下でないのでNG）
        When: _check_consecutive_decline()を呼ぶ
        Then: False
        """
        dates = _get_consecutive_school_days(today)
        entries = [
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[0],
                health_condition=4,
                mental_condition=5,
                reflection="day1",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[1],
                health_condition=4,
                mental_condition=5,
                reflection="day2",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[2],
                health_condition=4,
                mental_condition=4,
                reflection="day3",
            ),
        ]

        result = _check_consecutive_decline(entries)

        assert not result

    def test_health_decline_4_3_2_returns_true(
        self,
        student_user,
        today,
    ):
        """
        Given: 連続登校日で体調4→3→2（メンタルは横ばい）
        When: _check_consecutive_decline()を呼ぶ
        Then: True（体調が2ポイント低下、最終値2）
        """
        dates = _get_consecutive_school_days(today)
        entries = [
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[0],
                health_condition=4,
                mental_condition=4,
                reflection="day1",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[1],
                health_condition=3,
                mental_condition=4,
                reflection="day2",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[2],
                health_condition=2,
                mental_condition=4,
                reflection="day3",
            ),
        ]

        result = _check_consecutive_decline(entries)

        assert result

    def test_non_consecutive_dates_returns_false(
        self,
        student_user,
        today,
    ):
        """
        Given: 連続登校日でない日付（2日飛ばし）でメンタル5→4→3
        When: _check_consecutive_decline()を呼ぶ
        Then: False（連続登校日でない）
        """
        entries = [
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today - timedelta(days=6),
                health_condition=4,
                mental_condition=5,
                reflection="day1",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=today - timedelta(days=3),
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

        result = _check_consecutive_decline(entries)

        assert not result

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
        dates = _get_consecutive_school_days(today)
        entries = [
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[0],
                health_condition=4,
                mental_condition=4,
                reflection="day1",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[1],
                health_condition=4,
                mental_condition=4,
                reflection="day2",
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[2],
                health_condition=4,
                mental_condition=4,
                reflection="day3",
            ),
        ]

        result = _check_consecutive_decline(entries)

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

        result = _check_consecutive_decline(entries)

        assert not result

    def test_all_read_entries_returns_false(
        self,
        student_user,
        today,
    ):
        """
        Given: 3日連続低下だが全件既読
        When: _check_consecutive_decline()を呼ぶ
        Then: False（対応済みとみなす）
        """
        dates = _get_consecutive_school_days(today)
        entries = [
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[0],
                health_condition=4,
                mental_condition=5,
                reflection="day1",
                is_read=True,
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[1],
                health_condition=4,
                mental_condition=4,
                reflection="day2",
                is_read=True,
            ),
            DiaryEntry.objects.create(
                student=student_user,
                entry_date=dates[2],
                health_condition=4,
                mental_condition=3,
                reflection="day3",
                is_read=True,
            ),
        ]

        result = _check_consecutive_decline(entries)

        assert not result


@pytest.mark.django_db
class TestFindCriticalEntry:
    """_find_critical_entry()のテスト"""

    def test_mental_1_pending_returns_entry(
        self,
        student_user,
        today,
    ):
        """
        Given: メンタル★1、action_status=PENDING
        When: _find_critical_entry()を呼ぶ
        Then: そのエントリーを返す
        """
        yesterday = get_previous_school_day(today)
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=1,
            reflection="つらい",
            action_status=ActionStatus.PENDING,
        )

        result = _find_critical_entry([entry], today, yesterday)

        assert result == entry

    def test_health_1_pending_returns_entry(
        self,
        student_user,
        today,
    ):
        """
        Given: 体調★1、action_status=PENDING
        When: _find_critical_entry()を呼ぶ
        Then: そのエントリーを返す
        """
        yesterday = get_previous_school_day(today)
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=yesterday,
            health_condition=1,
            mental_condition=4,
            reflection="体調悪い",
            action_status=ActionStatus.PENDING,
        )

        result = _find_critical_entry([entry], today, yesterday)

        assert result == entry

    def test_mental_1_completed_and_read_returns_none(
        self,
        student_user,
        teacher_user,
        today,
    ):
        """
        Given: メンタル★1、is_read=True、action_status=COMPLETED
        When: _find_critical_entry()を呼ぶ
        Then: None（対応済み）
        """
        yesterday = get_previous_school_day(today)
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=1,
            reflection="つらい",
            is_read=True,
            action_status=ActionStatus.COMPLETED,
            action_completed_by=teacher_user,
            action_completed_at=timezone.now(),
        )

        result = _find_critical_entry([entry], today, yesterday)

        assert result is None

    def test_mental_1_read_but_pending_returns_entry(
        self,
        student_user,
        today,
    ):
        """
        Given: メンタル★1、is_read=True、action_status=PENDING
        When: _find_critical_entry()を呼ぶ
        Then: エントリーを返す（既読だがまだ対応していない）
        """
        yesterday = get_previous_school_day(today)
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=1,
            reflection="つらい",
            is_read=True,
            action_status=ActionStatus.PENDING,
        )

        result = _find_critical_entry([entry], today, yesterday)

        assert result == entry

    def test_past_unread_critical_found(
        self,
        student_user,
        today,
    ):
        """
        Given: 2日前にメンタル★1（未読）、今日はメンタル4
        When: _find_critical_entry()を呼ぶ
        Then: 2日前のエントリーを返す
        """
        yesterday = get_previous_school_day(today)
        old_entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=1,
            reflection="昨日つらかった",
            is_read=False,
        )
        new_entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="今日は普通",
        )

        # recent_entries は最新順
        result = _find_critical_entry([new_entry, old_entry], today, yesterday)

        assert result == old_entry


@pytest.mark.django_db
class TestIsCritical:
    """_is_critical()の後方互換テスト"""

    def test_is_critical_mental_1_pending_returns_true(
        self,
        student_user,
        today,
    ):
        """
        Given: メンタル★1、action_status=PENDING
        When: _is_critical()を4引数で呼ぶ
        Then: True
        """
        yesterday = get_previous_school_day(today)
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=1,
            reflection="つらい",
            action_status=ActionStatus.PENDING,
        )

        result = _is_critical(entry, [entry], today, yesterday)

        assert result

    def test_is_critical_mental_1_completed_returns_false(
        self,
        student_user,
        teacher_user,
        today,
    ):
        """
        Given: メンタル★1、action_status=COMPLETED
        When: _is_critical()を4引数で呼ぶ
        Then: False（既にトリアージ済み）
        """
        yesterday = get_previous_school_day(today)
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=yesterday,
            health_condition=4,
            mental_condition=1,
            reflection="つらい",
            is_read=True,
            action_status=ActionStatus.COMPLETED,
            action_completed_by=teacher_user,
            action_completed_at=timezone.now(),
        )

        result = _is_critical(entry, [entry], today, yesterday)

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
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            internal_action="parent_contact",
            action_status=ActionStatus.PENDING,
        )

        result = _needs_action(entry)

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
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="テスト",
            internal_action="",
            action_status=ActionStatus.PENDING,
        )

        result = _needs_action(entry)

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

        result = _needs_action(entry)

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

        result = format_inline_history(entries)

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
        result = format_inline_history([])

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
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection="短いテキスト",
        )

        result = get_snippet(entry)

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
        long_text = "あ" * 60
        entry = DiaryEntry.objects.create(
            student=student_user,
            entry_date=today,
            health_condition=4,
            mental_condition=4,
            reflection=long_text,
        )

        result = get_snippet(entry)

        assert len(result) == 53  # 50 + "..."
        assert result.endswith("...")

    def test_get_snippet_none_entry_returns_empty_string(self):
        """
        Given: entry=None
        When: get_snippet()を呼ぶ
        Then: 空文字列
        """
        result = get_snippet(None)

        assert result == ""


class TestAreConsecutiveSchoolDays:
    """are_consecutive_school_days()のテスト"""

    def test_mon_tue_wed_returns_true(self):
        """月火水は連続登校日"""
        from datetime import date

        from school_diary.diary.utils import are_consecutive_school_days

        # 2026-03-09 is Monday
        dates = [date(2026, 3, 9), date(2026, 3, 10), date(2026, 3, 11)]
        assert are_consecutive_school_days(dates)

    def test_thu_fri_mon_returns_true(self):
        """木金月は連続登校日（土日スキップ）"""
        from datetime import date

        from school_diary.diary.utils import are_consecutive_school_days

        # 2026-03-05 is Thursday
        dates = [date(2026, 3, 5), date(2026, 3, 6), date(2026, 3, 9)]
        assert are_consecutive_school_days(dates)

    def test_mon_wed_fri_returns_false(self):
        """月水金は連続登校日ではない"""
        from datetime import date

        from school_diary.diary.utils import are_consecutive_school_days

        dates = [date(2026, 3, 9), date(2026, 3, 11), date(2026, 3, 13)]
        assert not are_consecutive_school_days(dates)

    def test_single_date_returns_true(self):
        """1日だけの場合はTrue"""
        from datetime import date

        from school_diary.diary.utils import are_consecutive_school_days

        assert are_consecutive_school_days([date(2026, 3, 9)])

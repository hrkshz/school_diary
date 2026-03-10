"""Alert Service for Inbox Pattern (Teacher Dashboard)

This module provides backend logic for classifying students into 5 tiers + subsections:

Main tiers:
- Important (P0): Mental/Health ★1（未対応の過去エントリーも含む）
- Needs Attention (P1): 連続登校日3日間でmental/healthが2ポイント以上低下、最終値3以下
- Needs Action (P1.5): internal_action set and pending/in-progress
- Needs Response (P2): Daily tasks
  - P2-1: Not submitted (yesterday's diary missing)
  - P2-2: Unread (submitted today but not read)
- Completed (P3): Read + reaction selected, past 3 days only

Design principles:
- N+1 problem avoidance (bulk fetch + Python classification)
- Medical triage model (inspired by emergency room prioritization)
- Separation of concerns (business logic separated from views)
- Subsection pattern (Gmail/Trello/Jira style)
"""

from collections import defaultdict
from datetime import timedelta

from django.utils import timezone

from ..constants import AlertThresholds
from ..models import ActionStatus
from ..models import DiaryEntry
from ..utils import are_consecutive_school_days
from ..utils import get_previous_school_day


def classify_students(classroom):
    """生徒を5段階に分類（Inbox Pattern + サブセクション）

    Args:
        classroom: ClassRoomインスタンス

    Returns:
        dict: {
            'important': [(student, entry), ...],          # P0: 重要（トリガーエントリー付き）
            'needs_attention': [student, ...],              # P1: 3日連続低下（要注意）
            'needs_action': [(student, entry), ...],        # P1.5: 要対応タスク
            'not_submitted': [student, ...],                # P2-1: 未提出
            'unread': [student, ...],                       # P2-2: 未読
            'completed': [(student, date), ...]             # P3: 対応済み（日付付き）
        }

    Performance:
        - N+1問題回避: 一括取得（2-3クエリ）
        - 35名クラスで数ミリ秒
    """
    today = timezone.now().date()
    yesterday = get_previous_school_day(today)

    # 1. 全生徒の過去7日分を一括取得（N+1問題回避）
    all_recent_entries = (
        DiaryEntry.objects.filter(
            student__classes=classroom,
            entry_date__gte=today - timedelta(days=AlertThresholds.P0_LOOKBACK_DAYS),
        )
        .select_related("student")
        .order_by("student", "-entry_date")
    )

    # 2. Pythonで生徒ごとに分類（メモリ内処理）
    entries_by_student = defaultdict(list)
    for entry in all_recent_entries:
        entries_by_student[entry.student_id].append(entry)

    # 3. 各生徒を分類（排他的、優先度順）
    important = []
    needs_attention = []
    needs_action = []
    not_submitted = []
    unread = []
    completed = []

    for student in classroom.students.all():
        recent_entries = entries_by_student.get(student.id, [])
        latest_entry = recent_entries[0] if recent_entries else None

        # P0: 重要（mental/health ★1、過去の未対応エントリーも含む）
        critical_entry = _find_critical_entry(recent_entries, today, yesterday)
        if critical_entry:
            important.append((student, critical_entry))
            continue

        # P1: 要注意（連続登校日3日間で2ポイント以上低下、最終値3以下）
        if _check_consecutive_decline(recent_entries):
            needs_attention.append(student)
            continue

        # P1.5: 要対応タスク（internal_actionが設定され、対応待ち）
        if _needs_action(latest_entry):
            needs_action.append((student, latest_entry))
            continue

        # P2-1: 未提出（エントリーなし or 昨日より古い）
        if not latest_entry or latest_entry.entry_date < yesterday:
            not_submitted.append(student)
            continue

        # P2-2: 未読
        if not latest_entry.is_read:
            unread.append(student)
            continue

        # P3: 対応済み（前登校日以降のみ表示、土日を考慮）
        if latest_entry.entry_date >= yesterday:
            completed.append((student, latest_entry.entry_date))

    return {
        "important": important,
        "needs_attention": needs_attention,
        "needs_action": needs_action,
        "not_submitted": not_submitted,
        "unread": unread,
        "completed": completed,
    }


def _find_critical_entry(recent_entries, today, yesterday):
    """過去7日の未対応エントリーからP0対象を検索

    条件:
    - mental_condition == 1 OR health_condition == 1
    - 除外: is_read=True AND action_status in [COMPLETED, NOT_REQUIRED]

    Args:
        recent_entries: DiaryEntryのリスト（最新順）
        today: 今日の日付
        yesterday: 前登校日の日付

    Returns:
        DiaryEntry or None: P0対象エントリー（最新のもの）
    """
    critical_value = AlertThresholds.CRITICAL_CONDITION

    for entry in recent_entries:
        # mental/health どちらかが★1
        is_critical = (
            entry.mental_condition == critical_value
            or entry.health_condition == critical_value
        )
        if not is_critical:
            continue

        # 対応完了済みは除外
        is_resolved = entry.is_read and entry.action_status in (
            ActionStatus.COMPLETED,
            ActionStatus.NOT_REQUIRED,
        )
        if is_resolved:
            continue

        return entry

    return None


def _check_consecutive_decline(recent_entries):
    """連続登校日3日間でmental/healthが低下しているかチェック

    条件:
    - 3件が連続登校日であること
    - day1 >= day2 >= day3（単調非増加）
    - day1 - day3 >= 2（合計2ポイント以上低下）
    - day3 <= 3（最終値が「普通」以下）
    - 3件すべて既読の場合は除外

    Args:
        recent_entries: DiaryEntryのリスト（最新順）

    Returns:
        bool: 連続低下パターンが検出された場合True
    """
    if len(recent_entries) < AlertThresholds.DECLINE_CONSECUTIVE_DAYS:
        return False

    # 最新3件を古い順に取得
    entries = sorted(recent_entries[:3], key=lambda e: e.entry_date)

    # 連続登校日かチェック
    dates = [e.entry_date for e in entries]
    if not are_consecutive_school_days(dates):
        return False

    # 3件すべて既読なら除外（対応済みとみなす）
    if all(e.is_read for e in entries):
        return False

    min_drop = AlertThresholds.DECLINE_MIN_DROP
    max_final = AlertThresholds.DECLINE_MAX_FINAL

    # mental_condition チェック
    if _is_declining(
        entries[0].mental_condition,
        entries[1].mental_condition,
        entries[2].mental_condition,
        min_drop,
        max_final,
    ):
        return True

    # health_condition チェック
    if _is_declining(
        entries[0].health_condition,
        entries[1].health_condition,
        entries[2].health_condition,
        min_drop,
        max_final,
    ):
        return True

    return False


def _is_declining(day1, day2, day3, min_drop, max_final):
    """3日間の値が低下パターンに一致するかチェック

    Args:
        day1, day2, day3: 各日の値（古い順）
        min_drop: 最小低下ポイント
        max_final: 最終値の上限

    Returns:
        bool: 低下パターンの場合True
    """
    return bool(
        day1 >= day2 >= day3
        and (day1 - day3) >= min_drop
        and day3 <= max_final
    )


def _is_critical(latest_entry, recent_entries=None, today=None, yesterday=None):
    """Criticalに分類されるかチェック（後方互換性のためのラッパー）

    新しいロジックは _find_critical_entry() を使用。
    テストとの互換性のために残す。
    """
    if recent_entries is not None and today is not None and yesterday is not None:
        return _find_critical_entry(recent_entries, today, yesterday) is not None

    # レガシー: 引数1つの場合
    if not latest_entry:
        return False
    if latest_entry.action_status != ActionStatus.PENDING:
        return False
    return latest_entry.mental_condition == AlertThresholds.CRITICAL_CONDITION


def _needs_action(latest_entry):
    """要対応タスクに分類されるかチェック

    条件:
    - internal_actionが設定されている
    - action_statusがPENDINGまたはIN_PROGRESS

    Args:
        latest_entry: 最新のDiaryEntry（またはNone）

    Returns:
        bool: 要対応タスクに分類される場合True
    """
    if not latest_entry:
        return False

    # internal_actionが設定されている
    if not latest_entry.internal_action:
        return False

    # action_statusがPENDINGまたはIN_PROGRESS
    return latest_entry.action_status in (ActionStatus.PENDING, ActionStatus.IN_PROGRESS)


def format_inline_history(entries):
    """直近3日の履歴をインライン表示用にフォーマット

    Args:
        entries: DiaryEntryのリスト（最新順、最大3件）

    Returns:
        str: "10/14(★★★★)→10/15(★★★)→10/16(★★)" 形式

    Example:
        >>> entries = [entry1, entry2, entry3]  # 新しい順
        >>> format_inline_history(entries)
        "10/14(★★★★)→10/15(★★★)→10/16(★★)"
    """
    if not entries:
        return ""

    # 古い順にソート（左から右へ時系列）
    entries_sorted = sorted(entries[:3], key=lambda e: e.entry_date)

    parts = []
    for entry in entries_sorted:
        date_str = entry.entry_date.strftime("%m/%d")
        # メンタルを優先表示
        stars = "★" * entry.mental_condition
        parts.append(f"{date_str}({stars})")

    return "→".join(parts)


def get_snippet(entry, max_length=50):
    """連絡帳本文のスニペットを生成

    Args:
        entry: DiaryEntryインスタンス
        max_length: 最大文字数（デフォルト50）

    Returns:
        str: スニペット（50文字を超える場合は"..."を追加）

    Example:
        >>> entry.reflection = "今日は部活で先輩に怒られました..."  # 60文字
        >>> get_snippet(entry)
        "今日は部活で先輩に怒られました。理由がよく分からないので..."  # 50文字 + "..."
    """
    if not entry or not entry.reflection:
        return ""

    text = entry.reflection.strip()

    if len(text) <= max_length:
        return text

    return text[:max_length] + "..."

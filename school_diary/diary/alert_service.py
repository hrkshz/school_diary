"""Alert Service for Inbox Pattern (Teacher Dashboard)

This module provides backend logic for classifying students into 4 tiers + subsections:

Main tiers:
- Important (P0): Mental★1, immediate action required
- Needs Attention (P1): 3-day consecutive mental decline, early detection
- Needs Response (P2): Daily tasks
  - P2-1: Not submitted (yesterday's diary missing)
  - P2-2: Unread (submitted today but not read)
  - P2-3: No reaction (read but no reaction selected)
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

from .models import DiaryEntry
from .utils import get_previous_school_day


def classify_students(classroom):
    """生徒を4段階に分類（Inbox Pattern + サブセクション）

    Args:
        classroom: ClassRoomインスタンス

    Returns:
        dict: {
            'important': [student1, ...],      # P0: メンタル★1（重要）
            'needs_attention': [student2, ...], # P1: 3日連続低下（要注意）
            'not_submitted': [student3, ...],   # P2-1: 未提出
            'unread': [student4, ...],          # P2-2: 未読
            'no_reaction': [student5, ...],     # P2-3: 反応未選択
            'completed': [(student6, date), ...] # P3: 対応済み（日付付き）
        }

    Performance:
        - N+1問題回避: 一括取得（2-3クエリ）
        - 35名クラスで数ミリ秒
    """
    today = timezone.now().date()
    yesterday = get_previous_school_day(today)

    # 1. 全生徒の過去7日分を一括取得（N+1問題回避）
    all_recent_entries = DiaryEntry.objects.filter(
        student__classes=classroom,
        entry_date__gte=today - timedelta(days=7),
    ).select_related("student").order_by("student", "-entry_date")

    # 2. Pythonで生徒ごとに分類（メモリ内処理）
    entries_by_student = defaultdict(list)
    for entry in all_recent_entries:
        entries_by_student[entry.student_id].append(entry)

    # 3. 各生徒を分類（排他的、優先度順）
    important = []
    needs_attention = []
    not_submitted = []
    unread = []
    no_reaction = []
    completed = []

    for student in classroom.students.all():
        recent_entries = entries_by_student.get(student.id, [])
        latest_entry = recent_entries[0] if recent_entries else None

        # P0: 重要（メンタル★1、最優先）
        if _is_critical(latest_entry, recent_entries, today, yesterday):
            important.append(student)
            continue

        # P1: 要注意（3日連続メンタル低下）
        if _check_consecutive_decline(recent_entries):
            needs_attention.append(student)
            continue

        # P2-1: 未提出（エントリーなし or 昨日より古い）
        if not latest_entry or latest_entry.entry_date < yesterday:
            not_submitted.append(student)
            continue

        # P2-2: 未読
        if not latest_entry.is_read:
            unread.append(student)
            continue

        # P2-3: 反応未選択（既読だが反応なし）
        if latest_entry.is_read and not latest_entry.public_reaction:
            no_reaction.append(student)
            continue

        # P3: 対応済み（前登校日以降のみ表示、土日を考慮）
        if latest_entry.entry_date >= yesterday:
            completed.append((student, latest_entry.entry_date))

    return {
        "important": important,
        "needs_attention": needs_attention,
        "not_submitted": not_submitted,
        "unread": unread,
        "no_reaction": no_reaction,
        "completed": completed,
    }


def _check_consecutive_decline(recent_entries):
    """3日連続でメンタルが低下しているかチェック

    定義: day1 ≥ day2 ≥ day3 AND day3 < day1
    例: ★★★★★ → ★★★★ → ★★★ は True

    Args:
        recent_entries: DiaryEntryのリスト（最新順）

    Returns:
        bool: 3日連続低下の場合True
    """
    if len(recent_entries) < 3:
        return False

    # 最新3件を古い順に取得
    entries = sorted(recent_entries[:3], key=lambda e: e.entry_date)

    day1_mental = entries[0].mental_condition
    day2_mental = entries[1].mental_condition
    day3_mental = entries[2].mental_condition

    # 連続低下: day1 >= day2 >= day3 AND day3 < day1
    return bool(day1_mental >= day2_mental >= day3_mental and day3_mental < day1_mental)


def _is_critical(latest_entry, recent_entries, today, yesterday):
    """Criticalに分類されるかチェック

    条件:
    - メンタル★1（最優先）
    """
    if not latest_entry:
        return False

    # メンタル★1
    return latest_entry.mental_condition == 1


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

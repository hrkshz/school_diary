"""Alert Service for Inbox Pattern (Teacher Dashboard)

This module provides backend logic for classifying students into 3 tiers:
- Critical: Immediate action required (mental★1, 3-day decline, urgent action)
- High: Action needed today (mental★★, yesterday no submission, health★★)
- Normal: Observation mode (healthy, submitted, no alerts)

Design principles:
- N+1 problem avoidance (bulk fetch + Python classification)
- Medical triage model (inspired by emergency room prioritization)
- Separation of concerns (business logic separated from views)
"""

from datetime import timedelta
from django.utils import timezone
from collections import defaultdict

from .models import DiaryEntry


def classify_students(classroom):
    """生徒を3段階に分類（Critical / High / Normal）

    Args:
        classroom: ClassRoomインスタンス

    Returns:
        dict: {
            'critical': [student1, student2, ...],  # 要対応（即日）
            'high': [student3, student4, ...],      # 要確認（本日中）
            'normal': [student5, student6, ...]     # 正常（様子見）
        }

    Performance:
        - N+1問題回避: 一括取得（2-3クエリ）
        - 35名クラスで数ミリ秒
    """
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    # 1. 全生徒の過去7日分を一括取得（N+1問題回避）
    all_recent_entries = DiaryEntry.objects.filter(
        student__classes=classroom,
        entry_date__gte=today - timedelta(days=7)
    ).select_related('student').order_by('student', '-entry_date')

    # 2. Pythonで生徒ごとに分類（メモリ内処理）
    entries_by_student = defaultdict(list)
    for entry in all_recent_entries:
        entries_by_student[entry.student_id].append(entry)

    # 3. 各生徒を分類
    critical = []
    high = []
    normal = []

    for student in classroom.students.all():
        recent_entries = entries_by_student.get(student.id, [])
        latest_entry = recent_entries[0] if recent_entries else None

        # 分類ロジック
        if _is_critical(latest_entry, recent_entries, today, yesterday):
            critical.append(student)
        elif _is_high(latest_entry, recent_entries, today, yesterday):
            high.append(student)
        else:
            normal.append(student)

    return {
        'critical': critical,
        'high': high,
        'normal': normal
    }


def _is_critical(latest_entry, recent_entries, today, yesterday):
    """Criticalに分類されるかチェック

    条件:
    - メンタル★1（最優先）
    - 3日連続低下（後で実装）
    - 対応記録が「緊急」（後で実装）
    """
    if not latest_entry:
        return False

    # メンタル★1
    if latest_entry.mental_condition == 1:
        return True

    return False


def _is_high(latest_entry, recent_entries, today, yesterday):
    """Highに分類されるかチェック

    条件:
    - メンタル★★
    - 体調★★
    - 昨日未提出（最終提出が2日以上前）
    """
    if not latest_entry:
        # 昨日未提出（エントリーなし）
        return True

    # 最終提出日が昨日より古い = 昨日未提出
    if latest_entry.entry_date < yesterday:
        return True

    # メンタル★★
    if latest_entry.mental_condition == 2:
        return True

    # 体調★★
    if latest_entry.health_condition == 2:
        return True

    return False


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

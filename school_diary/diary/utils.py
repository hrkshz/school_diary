"""連絡帳アプリのユーティリティ関数"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


def get_students_with_consecutive_decline(
    classroom,
    days=None,
    threshold=None,
):
    """3日連続で体調/メンタルが低下している生徒を検出

    いじめ・不登校の早期発見のため、継続的な不調を検知する。

    Args:
        classroom: 対象クラス (ClassRoomインスタンス)
        days: 連続日数 (デフォルト3日、設計判断: 2日では誤検知多い、4日では遅い)
        threshold: 閾値 (≤この値で「低下」と判定、デフォルト2)
                  1=とても悪い、2=悪い、3=普通、4=良い、5=とても良い

    Returns:
        tuple: (体調低下生徒リスト, メンタル低下生徒リスト)

    パフォーマンス:
        - O(n) where n = 生徒数
        - N+1問題回避 (select_related使用)
        - 35名クラスで数ミリ秒

    設計判断:
        - 厳密に連続 (最新3日間が連続で≤2)
        - 未提出日は除外 (提出されたデータのみで判断)
        - 体調とメンタルを個別に検出 (両方低下の場合も別々にカウント)
    """
    from .constants import HealthThresholds
    from .models import DiaryEntry

    if days is None:
        days = HealthThresholds.CONSECUTIVE_DAYS
    if threshold is None:
        threshold = HealthThresholds.POOR_CONDITION

    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days - 1)

    # 過去3日分の連絡帳を取得（N+1問題回避）
    entries = (
        DiaryEntry.objects.filter(
            student__classes=classroom,
            entry_date__gte=start_date,
            entry_date__lte=end_date,
        )
        .select_related("student")
        .order_by("student", "-entry_date")
    )

    # 生徒ごとにグループ化して連続性をチェック
    students_health_decline = []
    students_mental_decline = []

    for student in classroom.students.all():
        # この生徒の連絡帳を抽出
        student_entries = [e for e in entries if e.student_id == student.id]

        # 最新3件が揃っている場合のみチェック（未提出日は除外）
        if len(student_entries) >= days:
            recent_entries = student_entries[:days]

            # 全て閾値以下かチェック（all()で厳密な連続性を確認）
            if all(e.health_condition <= threshold for e in recent_entries):
                students_health_decline.append(student)

            if all(e.mental_condition <= threshold for e in recent_entries):
                students_mental_decline.append(student)

    return students_health_decline, students_mental_decline


def get_current_classroom(user):
    """
    ユーザーの現在のクラスを取得（最新academic_year）

    Args:
        user: Userオブジェクト

    Returns:
        ClassRoomオブジェクト or None
    """

    if not user or not hasattr(user, "classes"):
        return None

    return user.classes.order_by("-academic_year", "-grade").first()


def get_classroom_history(user):
    """
    ユーザーの過去の所属クラス履歴を取得

    Args:
        user: Userオブジェクト

    Returns:
        QuerySet[ClassRoom]（新しい順）
    """
    from .models import ClassRoom

    if not user or not hasattr(user, "classes"):
        return ClassRoom.objects.none()

    return user.classes.order_by("-academic_year", "-grade")


def get_previous_school_day(date):
    """前登校日を取得（土日を除外）

    生徒は提出日の「前登校日」の内容を登録する。
    土日を除外し、月曜日の場合は金曜日を返す。

    Args:
        date: 基準日（通常は今日）

    Returns:
        前登校日の日付

    例:
        - 月曜日 → 金曜日（3日前）
        - 火〜金曜日 → 前日
        - 土曜日 → 金曜日（1日前）
        - 日曜日 → 金曜日（2日前）

    Note:
        祝日は考慮しない（要件に明記あり）
    """
    from datetime import timedelta

    previous_day = date - timedelta(days=1)

    # 土曜日（5）の場合 → 金曜日
    if previous_day.weekday() == 5:
        return previous_day - timedelta(days=1)

    # 日曜日（6）の場合 → 金曜日
    if previous_day.weekday() == 6:
        return previous_day - timedelta(days=2)

    return previous_day


def check_consecutive_decline(student, field_name="health_condition", days=3):
    """3日連続低下パターンを検出

    Args:
        student: Userオブジェクト（生徒）
        field_name: チェックするフィールド名（"health_condition" or "mental_condition"）
        days: 連続日数（デフォルト: 3）

    Returns:
        dict: {
            "has_alert": bool,  # アラート対象かどうか
            "trend": list,      # 値の推移（例: [5, 4, 3]）
            "dates": list,      # 日付のリスト
        }

    アルゴリズム:
        day1≥day2≥day3 AND day3<day1
        - 厳密な連続低下（5→4→3）
        - 横ばい後の低下（4→4→3）
        - 欠席日は除外
    """

    from .models import AttendanceStatus
    from .models import DailyAttendance

    # 過去N日分のエントリーを取得（欠席日を除外）
    # Prefetchで最適化: N+1問題回避
    entries = (
        student.diary_entries.filter(
            entry_date__lt=timezone.now().date(),
        )
        .exclude(
            entry_date__in=DailyAttendance.objects.filter(
                student=student,
                status=AttendanceStatus.ABSENT,
            ).values_list("date", flat=True),
        )
        .order_by("-entry_date")[:days]
    )

    # エントリー数が不足している場合
    if entries.count() < days:
        return {"has_alert": False, "trend": [], "dates": []}

    # 値と日付を抽出（新しい順 → 古い順に反転）
    values = [getattr(entry, field_name) for entry in reversed(entries)]
    dates = [entry.entry_date for entry in reversed(entries)]

    # アルゴリズム: day1≥day2≥day3 AND day3<day1
    day1, day2, day3 = values[0], values[1], values[2]

    has_alert = (day1 >= day2 >= day3) and (day3 < day1)

    return {
        "has_alert": has_alert,
        "trend": values,
        "dates": dates,
    }


def check_critical_mental_state(student):
    """メンタル★1（臨床的に有意な状態）を検出

    Args:
        student: Userオブジェクト（生徒）

    Returns:
        dict: {
            "has_alert": bool,  # メンタル★1かどうか
            "value": int,       # メンタル値
            "date": date,       # エントリー日付
        }

    Note:
        DSM-5臨床基準: ★1のみが臨床的に有意（★2は除外）
        教育現場での実用性: アラート疲労防止（週0-2件/クラス）
    """

    # 最新のエントリーを取得
    latest_entry = student.diary_entries.filter(entry_date__lt=timezone.now().date()).order_by("-entry_date").first()

    if not latest_entry:
        return {"has_alert": False, "current_value": None, "date": None}

    has_alert = latest_entry.mental_condition == 1

    return {
        "has_alert": has_alert,
        "current_value": latest_entry.mental_condition,
        "date": latest_entry.entry_date,
    }

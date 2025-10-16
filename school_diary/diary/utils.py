"""連絡帳アプリのユーティリティ関数"""

from django.contrib.auth import get_user_model

User = get_user_model()


def get_current_classroom(user):
    """
    ユーザーの現在のクラスを取得（最新academic_year）

    Args:
        user: Userオブジェクト

    Returns:
        ClassRoomオブジェクト or None
    """
    from .models import ClassRoom

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
    from datetime import date as date_class
    from .models import DailyAttendance, AttendanceStatus

    # 過去N日分のエントリーを取得（欠席日を除外）
    # Prefetchで最適化: N+1問題回避
    entries = (
        student.diary_entries.filter(
            entry_date__lt=date_class.today()
        )
        .exclude(
            entry_date__in=DailyAttendance.objects.filter(
                student=student,
                status=AttendanceStatus.ABSENT
            ).values_list("date", flat=True)
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
    from datetime import date as date_class

    # 最新のエントリーを取得
    latest_entry = (
        student.diary_entries
        .filter(entry_date__lt=date_class.today())
        .order_by("-entry_date")
        .first()
    )

    if not latest_entry:
        return {"has_alert": False, "current_value": None, "date": None}

    has_alert = latest_entry.mental_condition == 1

    return {
        "has_alert": has_alert,
        "current_value": latest_entry.mental_condition,
        "date": latest_entry.entry_date,
    }

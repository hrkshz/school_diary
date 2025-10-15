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

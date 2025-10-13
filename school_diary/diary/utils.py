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

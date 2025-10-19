"""連絡帳システムの定数定義"""


class ConditionLevel:
    """体調・メンタルのレベル定数"""

    VERY_BAD = 1
    BAD = 2
    NORMAL = 3
    GOOD = 4
    VERY_GOOD = 5


class GradeLevel:
    """学年レベル定数"""

    GRADE_1 = 1
    GRADE_2 = 2
    GRADE_3 = 3


# 学年選択肢（共通定義）
GRADE_CHOICES = [
    (GradeLevel.GRADE_1, "1年"),
    (GradeLevel.GRADE_2, "2年"),
    (GradeLevel.GRADE_3, "3年"),
]

# 空欄付き学年選択肢
GRADE_CHOICES_WITH_EMPTY = [("", "---")] + GRADE_CHOICES


# ========================================
# views.py 用の定数（M-VIEWS-003）
# ========================================


class HealthThresholds:
    """体調・メンタル関連の閾値定数"""

    # 体調/メンタル低下の判定閾値
    # 1=とても悪い、2=悪い、3=普通、4=良い、5=とても良い
    # ≤この値で「低下」と判定
    POOR_CONDITION = 2

    # 連続低下の判定日数
    CONSECUTIVE_DAYS = 3

    # クラス全体の警告閾値（人数）
    CLASS_ALERT_THRESHOLD = 5


class NoteSettings:
    """担任メモ関連の設定"""

    # 担任メモの最小文字数
    MIN_NOTE_LENGTH = 10

    # 学年共有メモの表示期間（日数）
    SHARED_NOTE_DAYS = 3

    # 学年共有メモの表示件数上限
    SHARED_NOTE_LIMIT = 5


class DashboardSettings:
    """ダッシュボード関連の設定"""

    # 提出率警告閾値（%）
    SUBMISSION_RATE_WARNING = 80

    # 健康ダッシュボードでサポートする日数
    HEALTH_DASHBOARD_DAYS = [7, 14]

    # 健康ダッシュボードのデフォルト日数
    HEALTH_DASHBOARD_DEFAULT_DAYS = 7

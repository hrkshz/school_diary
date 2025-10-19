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

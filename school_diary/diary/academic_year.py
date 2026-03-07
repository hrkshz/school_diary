"""Academic year helpers."""

from datetime import date


def get_current_academic_year(today: date | None = None) -> int:
    """Return the current academic year in Japan.

    The school year starts in April and ends in March.
    """
    today = today or date.today()
    if today.month < 4:
        return today.year - 1
    return today.year

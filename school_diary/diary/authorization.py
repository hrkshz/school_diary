"""Authorization and access helpers for school diary roles."""

from django.contrib.auth import get_user_model
from django.db.models import Max
from django.db.models import Q

from .academic_year import get_current_academic_year
from .models import ClassRoom
from .models import UserProfile

User = get_user_model()


def get_user_role(user) -> str | None:
    """Return the user's profile role when available."""
    if not user or not getattr(user, "is_authenticated", False):
        return None
    profile = getattr(user, "profile", None)
    if not profile:
        return None
    return profile.role


def user_has_role(user, *roles: str) -> bool:
    """Check whether the user has one of the provided roles."""
    if getattr(user, "is_superuser", False):
        return True
    return get_user_role(user) in roles


def get_latest_academic_year() -> int:
    """Return the latest academic year in the database, or the current year."""
    latest_year = ClassRoom.objects.aggregate(Max("academic_year"))["academic_year__max"]
    return latest_year or get_current_academic_year()


def get_primary_classroom(user):
    """Return the user's primary classroom, preferring homeroom then assistant access."""
    if not user or not getattr(user, "is_authenticated", False):
        return None
    homeroom = (
        ClassRoom.objects.filter(homeroom_teacher=user)
        .order_by("-academic_year", "grade", "class_name")
        .first()
    )
    if homeroom:
        return homeroom
    return (
        ClassRoom.objects.filter(assistant_teachers=user)
        .order_by("-academic_year", "grade", "class_name")
        .first()
    )


def get_teacher_classrooms(user):
    """Return classrooms accessible to a teacher via homeroom/assistant assignment."""
    if not user or not getattr(user, "is_authenticated", False):
        return ClassRoom.objects.none()
    return ClassRoom.objects.filter(
        Q(homeroom_teacher=user) | Q(assistant_teachers=user),
    ).distinct()


def get_accessible_classrooms(user):
    """Return classrooms the user can access according to role."""
    if not user or not getattr(user, "is_authenticated", False):
        return ClassRoom.objects.none()
    if user.is_superuser:
        return ClassRoom.objects.all()

    role = get_user_role(user)
    if role == UserProfile.ROLE_SCHOOL_LEADER:
        return ClassRoom.objects.all()
    if role == UserProfile.ROLE_GRADE_LEADER:
        managed_grade = getattr(user.profile, "managed_grade", None)
        if not managed_grade:
            return ClassRoom.objects.none()
        return ClassRoom.objects.filter(
            grade=managed_grade,
            academic_year=get_latest_academic_year(),
        )
    if role == UserProfile.ROLE_TEACHER:
        return get_teacher_classrooms(user)
    if role == UserProfile.ROLE_STUDENT:
        return user.classes.all()
    return ClassRoom.objects.none()


def get_accessible_students(user):
    """Return students visible to the given user."""
    if not user or not getattr(user, "is_authenticated", False):
        return User.objects.none()
    if user.is_superuser or get_user_role(user) == UserProfile.ROLE_SCHOOL_LEADER:
        return User.objects.all()
    if get_user_role(user) == UserProfile.ROLE_STUDENT:
        return User.objects.filter(id=user.id)
    return User.objects.filter(classes__in=get_accessible_classrooms(user)).distinct()


def can_access_classroom(user, classroom) -> bool:
    """Return True when the user can access the classroom."""
    if classroom is None:
        return False
    return get_accessible_classrooms(user).filter(id=classroom.id).exists()


def can_access_student(user, student) -> bool:
    """Return True when the user can access the student."""
    if student is None:
        return False
    return get_accessible_students(user).filter(id=student.id).exists()

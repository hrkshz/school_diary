from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from school_diary.diary.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = "Creates test users for school diary system."

    @transaction.atomic
    def handle(self, *args, **options):
        COMMON_PASSWORD = "password123"

        users_to_create = [
            {
                "username": "管理太郎",
                "email": "admin@example.com",
                "first_name": "管理",
                "last_name": "太郎",
                "is_staff": True,
                "is_superuser": True,
                "role": "admin",
                "managed_grade": None,
            },
            {
                "username": "校長次郎",
                "email": "principal@example.com",
                "first_name": "校長",
                "last_name": "次郎",
                "is_staff": True,
                "is_superuser": False,
                "role": "school_leader",
                "managed_grade": None,
            },
            {
                "username": "学年三郎",
                "email": "grade_leader@example.com",
                "first_name": "学年",
                "last_name": "三郎",
                "is_staff": True,
                "is_superuser": False,
                "role": "grade_leader",
                "managed_grade": 1,
            },
            {
                "username": "担任四郎",
                "email": "teacher@example.com",
                "first_name": "担任",
                "last_name": "四郎",
                "is_staff": True,
                "is_superuser": False,
                "role": "teacher",
                "managed_grade": None,
            },
            {
                "username": "生徒五郎",
                "email": "student@example.com",
                "first_name": "生徒",
                "last_name": "五郎",
                "is_staff": False,
                "is_superuser": False,
                "role": "student",
                "managed_grade": None,
            },
        ]

        for user_data in users_to_create:
            role = user_data.pop("role")
            managed_grade = user_data.pop("managed_grade")

            user, created = User.objects.get_or_create(
                username=user_data["username"],
                defaults=user_data,
            )

            if created:
                user.set_password(COMMON_PASSWORD)
                user.save()

                # UserProfile.role更新（signalで自動作成されたprofileを更新）
                profile = UserProfile.objects.get(user=user)
                profile.role = role
                if managed_grade:
                    profile.managed_grade = managed_grade
                profile.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"User '{user.username}' ({user.get_full_name()}) created."
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"User '{user.username}' already exists.")
                )

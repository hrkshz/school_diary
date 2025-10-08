from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import Group

User = get_user_model()

class Command(BaseCommand):
    help = "Creates test users and assigns them to groups."

    @transaction.atomic
    def handle(self, *args, **options):
        COMMON_PASSWORD = "password123"

        users_to_create = {
            "admin": {"name": "管理者 太郎", "group": "管理者", "is_staff": True, "is_superuser": True},
            "approver": {"name": "承認者 次郎", "group": "承認者", "is_staff": True, "is_superuser": False},
            "user": {"name": "一般 三郎", "group": "一般", "is_staff": False, "is_superuser": False},
            "auditor": {"name": "監査 四郎", "group": "監査者", "is_staff": True, "is_superuser": False},
            "editor": {"name": "編集者 五郎", "group": "編集者", "is_staff": True, "is_superuser": False},
        }

        for username_key, details in users_to_create.items():
            email = f"{username_key}@example.com"
            
            defaults_details = details.copy()
            group_name = defaults_details.pop("group")
            
            user, created = User.objects.get_or_create(
                email=email,
                defaults=defaults_details,
            )

            if created:
                user.set_password(COMMON_PASSWORD)
                try:
                    group = Group.objects.get(name=group_name)
                    user.groups.add(group)
                except Group.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Group '{group_name}' not found!"))
                user.save()
                self.stdout.write(self.style.SUCCESS(f"User '{email}' created."))
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from kits.demos.models import DemoRequest


class Command(BaseCommand):
    help = "Initializes user groups and assigns permissions."

    def handle(self, *args, **options):
        permissions_map = {
            "一般": [
                "add_demorequest",
                "view_demorequest",
            ],
            "承認者": [
                "change_demorequest",
                "view_demorequest",
            ],
            "管理者": [
                "add_demorequest",
                "change_demorequest",
                "view_demorequest",
                "delete_demorequest",
            ],
            # --- ここから下の2つを追加 ---
            "監査者": [
                "view_demorequest",
            ],
            "編集者": [
                "add_demorequest",
                "change_demorequest",
                "view_demorequest",
            ],
        }

        try:
            content_type = ContentType.objects.get_for_model(DemoRequest)
        except ContentType.DoesNotExist:
            self.stderr.write(self.style.ERROR("ContentType for DemoRequest not found."))
            return

        for group_name, perm_codenames in permissions_map.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Group "{group_name}" created.'))

            group.permissions.clear()
            permissions = Permission.objects.filter(
                content_type=content_type,
                codename__in=perm_codenames,
            )
            group.permissions.add(*permissions)
            self.stdout.write(
                self.style.SUCCESS(f'Permissions for "{group_name}" set.'),
            )

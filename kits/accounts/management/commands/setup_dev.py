from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

class Command(BaseCommand):
    help = "Sets up the development environment by creating groups and test users."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Starting Development Environment Setup ---"))

        # 1. グループ作成コマンドを呼び出す
        self.stdout.write("\nRunning setup_groups...")
        call_command("setup_groups")

        # 2. ユーザー作成コマンドを呼び出す
        self.stdout.write("\nRunning setup_test_users...")
        call_command("setup_test_users")

        self.stdout.write(self.style.SUCCESS("\n--- Development Environment Setup Complete! ---"))
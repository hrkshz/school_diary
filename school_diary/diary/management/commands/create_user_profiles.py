"""既存ユーザーにUserProfileを作成する管理コマンド"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from school_diary.diary.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = "既存ユーザーにUserProfileを作成します"

    def handle(self, *args, **options):
        """コマンド実行"""
        created_count = 0
        skipped_count = 0

        for user in User.objects.all():
            # 既にProfileがある場合はスキップ
            if hasattr(user, "profile"):
                skipped_count += 1
                continue

            # デフォルトで生徒として作成
            UserProfile.objects.create(
                user=user,
                role="student",
            )
            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"完了: {created_count}件のUserProfileを作成しました（スキップ: {skipped_count}件）"
            )
        )

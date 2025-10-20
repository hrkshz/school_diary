"""既存UserにUserProfileを作成する管理コマンド

使用方法:
    dj fix_userprofiles

目的:
    - post_saveシグナル実装前に作成されたUserにUserProfileがない問題を解決
    - 既存User全てにUserProfileとEmailAddressを作成
"""

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from school_diary.diary.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    """既存UserにUserProfileを作成する"""

    help = "既存User全てにUserProfileとEmailAddressを作成する"

    def handle(self, *_args, **_options):
        """コマンド実行"""
        users_without_profile = []
        users_with_profile = []

        for user in User.objects.all():
            # UserProfile存在確認
            if not hasattr(user, "profile"):
                users_without_profile.append(user)
            else:
                users_with_profile.append(user)

        self.stdout.write(f"既存User総数: {User.objects.count()}")
        self.stdout.write(
            self.style.SUCCESS(f"UserProfile有り: {len(users_with_profile)}"),
        )
        self.stdout.write(
            self.style.WARNING(f"UserProfile無し: {len(users_without_profile)}"),
        )

        if not users_without_profile:
            self.stdout.write(
                self.style.SUCCESS("全Userに既にUserProfileが存在します。"),
            )
            return

        # UserProfile作成
        created_profiles = 0
        for user in users_without_profile:
            UserProfile.objects.create(user=user, role="student")
            created_profiles += 1

            # EmailAddress作成（allauth連携）
            if user.email:
                EmailAddress.objects.get_or_create(
                    user=user,
                    email=user.email.lower(),
                    defaults={
                        "verified": settings.ACCOUNT_EMAIL_VERIFICATION != "mandatory",
                        "primary": True,
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(f"✅ {created_profiles}件のUserProfileを作成しました。"),
        )
        self.stdout.write("各Userのroleはデフォルト値（student）に設定されています。")
        self.stdout.write("管理画面で適切なroleに変更してください。")

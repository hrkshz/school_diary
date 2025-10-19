"""ヘルスチェックコマンド

起動時の自動診断:
- データベース接続
- ALLOWED_HOSTS設定
- EmailAddress整合性

Usage:
    dj healthcheck
"""

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import connection

User = get_user_model()


class Command(BaseCommand):
    """ヘルスチェックコマンド"""

    help = "システムヘルスチェック（起動診断）"

    def handle(self, *args, **options):
        """ヘルスチェック実行"""
        self.stdout.write(self.style.WARNING("=== システムヘルスチェック開始 ===\n"))

        errors = []
        warnings = []

        # 1. データベース接続チェック
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS("✅ データベース接続: OK"))
        except Exception as e:
            errors.append(f"❌ データベース接続エラー: {e}")
            self.stdout.write(self.style.ERROR(errors[-1]))

        # 2. ALLOWED_HOSTS チェック
        if settings.DEBUG:
            if settings.ALLOWED_HOSTS == ["*"]:
                self.stdout.write(
                    self.style.SUCCESS("✅ ALLOWED_HOSTS: OK（開発環境で全ホスト許可）"),
                )
            elif "localhost" not in settings.ALLOWED_HOSTS:
                warnings.append(
                    "⚠️  ALLOWED_HOSTS に localhost が含まれていません",
                )
                self.stdout.write(self.style.WARNING(warnings[-1]))
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}",
                    ),
                )
        elif settings.ALLOWED_HOSTS == ["*"]:
            errors.append(
                "❌ 本番環境で ALLOWED_HOSTS=['*'] は危険です",
            )
            self.stdout.write(self.style.ERROR(errors[-1]))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}",
                ),
            )

        # 3. EmailAddress整合性チェック
        users_without_email = []
        total_users = User.objects.count()
        users_with_email = User.objects.exclude(email="").count()

        for user in User.objects.exclude(email=""):
            if not EmailAddress.objects.filter(user=user).exists():
                users_without_email.append(user.username)

        if users_without_email:
            warnings.append(
                f"⚠️  EmailAddressレコードなし: {len(users_without_email)}人",
            )
            self.stdout.write(self.style.WARNING(warnings[-1]))
            for username in users_without_email[:5]:
                self.stdout.write(f"    - {username}")
            if len(users_without_email) > 5:
                self.stdout.write(f"    ... 他{len(users_without_email) - 5}人")
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ EmailAddress整合性: OK（{users_with_email}/{total_users}人）",
                ),
            )

        # 4. サマリー
        self.stdout.write("\n=== 結果 ===")
        if errors:
            self.stdout.write(self.style.ERROR(f"エラー: {len(errors)}件"))
            self.exit_code = 1
        else:
            self.stdout.write(self.style.SUCCESS("エラー: 0件"))

        if warnings:
            self.stdout.write(self.style.WARNING(f"警告: {len(warnings)}件"))
        else:
            self.stdout.write(self.style.SUCCESS("警告: 0件"))

        if not errors and not warnings:
            self.stdout.write(
                self.style.SUCCESS("\n✅ すべてのチェックが正常です"),
            )


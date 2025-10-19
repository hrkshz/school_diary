"""Djangoシグナル定義

User作成時に関連モデルを自動作成する。
"""

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """User作成時にUserProfileを自動作成する

    Args:
        sender: シグナル送信元（Userモデル）
        instance: 作成されたUserインスタンス
        created: 新規作成の場合True、更新の場合False
        **kwargs: その他のシグナル引数

    Note:
        - デフォルトrole="student"（UserProfileモデルのデフォルト値）
        - allauth用のEmailAddressレコードも自動作成
    """
    if created:
        # UserProfile自動作成
        UserProfile.objects.create(user=instance)

        # allauth EmailAddress 自動作成（メール認証連携）
        if instance.email:
            try:
                EmailAddress.objects.get_or_create(
                    user=instance,
                    email=instance.email.lower(),
                    defaults={
                        "verified": not settings.ACCOUNT_EMAIL_VERIFICATION
                        == "mandatory",
                        "primary": True,
                    },
                )
            except Exception:
                # EmailAddressの制約違反（同じemailが別userに既登録）は無視
                # 実運用では発生しないが、テストで重複email作成時に発生
                pass

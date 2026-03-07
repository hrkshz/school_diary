"""Djangoシグナル定義

User作成時に関連モデルを自動作成する。
"""

import logging

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile

User = get_user_model()
logger = logging.getLogger(__name__)


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
                        "verified": settings.ACCOUNT_EMAIL_VERIFICATION != "mandatory",
                        "primary": True,
                    },
                )
            except IntegrityError:
                logger.warning(
                    "EmailAddress creation skipped because the email already exists for another user",
                    extra={"user_id": instance.id, "email": instance.email.lower()},
                )

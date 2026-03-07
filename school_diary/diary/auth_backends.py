"""カスタム認証バックエンド

django-allauth 65.xで`login`パラメータが正しく処理されない問題を解決
"""

import logging

from allauth.account.auth_backends import AuthenticationBackend as AllauthAuthenticationBackend

logger = logging.getLogger(__name__)


class EmailAuthenticationBackend(AllauthAuthenticationBackend):
    """メールアドレス認証用のカスタムバックエンド

    django-allauthのLoginFormが送信する`login`フィールドを
    `email`フィールドに変換して処理します。
    """

    def authenticate(self, request, **credentials):
        # loginフィールドがある場合、emailフィールドに変換
        login = credentials.get("login")
        if login and "email" not in credentials:
            logger.info("EmailAuthenticationBackend: Converting login='%s' to email and username", login)

            # loginフィールドをemailとusernameの両方にコピー
            # これにより、どちらの形式でも認証が可能になる
            credentials = credentials.copy()
            credentials["email"] = login
            credentials["username"] = login

        # 親クラスのauthenticateメソッドを呼び出す
        result = super().authenticate(request, **credentials)

        identifier = credentials.get("email") or credentials.get("username")
        if result:
            logger.info("EmailAuthenticationBackend: Authentication successful for %s", identifier)
        else:
            logger.warning("EmailAuthenticationBackend: Authentication failed for %s", identifier)

        return result

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
            # デバッグログ
            logger.info(f"EmailAuthenticationBackend: Converting login='{login}' to email and username")

            # loginフィールドをemailとusernameの両方にコピー
            # これにより、どちらの形式でも認証が可能になる
            credentials = credentials.copy()
            credentials["email"] = login
            credentials["username"] = login

        # 親クラスのauthenticateメソッドを呼び出す
        result = super().authenticate(request, **credentials)

        # デバッグログ
        if result:
            logger.info(
                f"EmailAuthenticationBackend: Authentication successful for {credentials.get('email') or credentials.get('username')}"
            )
        else:
            logger.warning(
                f"EmailAuthenticationBackend: Authentication failed for {credentials.get('email') or credentials.get('username')}"
            )

        return result

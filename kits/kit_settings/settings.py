from django.conf import settings as django_settings


class KitsSettings:
    """
    kitsアプリ専用の設定を管理するクラス。

    プロジェクトのsettings.pyで定義された 'KITS_' プレフィックス付きの変数を読み込む。
    定義されていない場合は、このクラスで定義されたデフォルト値が使用される。
    """

    def __init__(self, prefix="KITS_"):
        self.prefix = prefix
        self.defaults = {
            "ACCOUNTS_GROUP_NAMES": ("一般", "承認者", "管理者"),
        }

    def __getattr__(self, name):
        """
        kits.conf.settings.FOO のようにアクセスされた時に呼ばれる。
        1. プロジェクト設定の 'KITS_FOO' を探す
        2. なければ、self.defaults の 'FOO' を返す
        3. どちらもなければ AttributeError を送出する
        """
        setting_key = f"{self.prefix}{name}"

        if hasattr(django_settings, setting_key):
            return getattr(django_settings, setting_key)

        if name in self.defaults:
            return self.defaults[name]

        msg = (
            f"'{name}' setting not found in KitsSettings defaults or project settings."
        )
        raise AttributeError(
            msg,
        )


# 'settings' という名前でインスタンスを公開する
settings = KitsSettings()

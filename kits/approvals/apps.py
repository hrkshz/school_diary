from contextlib import suppress

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ApprovalsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "kits.approvals"
    verbose_name = _("承認管理")

    def ready(self):
        """アプリケーション起動時にシグナルをインポートして登録する。"""
        with suppress(ImportError):
            import kits.approvals.signals

            _ = kits.approvals.signals  # Mark as used for linters

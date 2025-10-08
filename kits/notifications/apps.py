from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NotificationsConfig(AppConfig):
    name = "kits.notifications"
    verbose_name = _("通知管理")

    def ready(self):
        try:
            import kits.notifications.signals  # noqa: F401
        except ImportError:
            pass

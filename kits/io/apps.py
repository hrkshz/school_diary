"""Django app configuration for kits.io"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class IoConfig(AppConfig):
    """Configuration for the IO app"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "kits.io"
    verbose_name = _("データ入出力")

    def ready(self):
        """Initialize app when Django starts"""
        try:
            import kits.io.signals  # noqa: F401
        except ImportError:
            pass

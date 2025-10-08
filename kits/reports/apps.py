"""Django app configuration for reports"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ReportsConfig(AppConfig):
    """Reports app configuration"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "kits.reports"
    verbose_name = _("レポート管理")

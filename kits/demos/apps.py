from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DemosConfig(AppConfig):
    """
    Configuration class for the 'demos' app.
    This app provides dummy models for integration testing of the 'kits' components.
    """

    name = "kits.demos"
    verbose_name = _("デモ・参考実装")

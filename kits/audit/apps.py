"""
Audit trail configuration.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AuditConfig(AppConfig):
    """Configuration for the audit app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "kits.audit"
    verbose_name = _("監査証跡")

    def ready(self):
        """Import signals when app is ready."""
        try:
            import kits.audit.signals  # noqa: F401
        except ImportError:
            pass

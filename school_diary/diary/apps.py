from django.apps import AppConfig


class DiaryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "school_diary.diary"
    verbose_name = "連絡帳"

    def ready(self):
        """アプリ起動時の初期化処理"""
        # AuditLogを管理画面から削除（HistoricalUserProfileで十分）
        from django.contrib import admin
        from django.contrib.admin.exceptions import NotRegistered

        try:
            from kits.audit.models import AuditLog

            admin.site.unregister(AuditLog)
        except (ImportError, NotRegistered):
            pass  # audit未インストール、またはadmin登録されていない

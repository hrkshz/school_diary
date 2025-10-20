from django.apps import AppConfig


class DiaryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "school_diary.diary"
    verbose_name = "連絡帳"

    def ready(self):
        """アプリ起動時の初期化処理

        全アプリロード完了後に実行される。
        不要なkitsモデルを管理画面から除外（教師向けのシンプルな画面を実現）。
        """
        from django.contrib import admin
        from django.contrib.admin.exceptions import NotRegistered

        # kits.reports（レポート管理: 3モデル）
        try:
            from kits.reports.models import Report
            from kits.reports.models import ReportSchedule
            from kits.reports.models import ReportTemplate

            admin.site.unregister(Report)
            admin.site.unregister(ReportSchedule)
            admin.site.unregister(ReportTemplate)
        except (ImportError, NotRegistered):
            pass

        # kits.approvals（承認管理: 4モデル）
        try:
            from kits.approvals.models import ApprovalAction
            from kits.approvals.models import ApprovalRequest
            from kits.approvals.models import ApprovalStep
            from kits.approvals.models import ApprovalWorkflow

            admin.site.unregister(ApprovalWorkflow)
            admin.site.unregister(ApprovalStep)
            admin.site.unregister(ApprovalRequest)
            admin.site.unregister(ApprovalAction)
        except (ImportError, NotRegistered):
            pass

        # kits.notifications（通知管理: 2モデル）
        try:
            from kits.notifications.models import Notification
            from kits.notifications.models import NotificationTemplate

            admin.site.unregister(Notification)
            admin.site.unregister(NotificationTemplate)
        except (ImportError, NotRegistered):
            pass

        # kits.demos（デモ・参考実装: 1モデル）
        try:
            from kits.demos.models import DemoRequest

            admin.site.unregister(DemoRequest)
        except (ImportError, NotRegistered):
            pass

        # シグナル登録（User作成時にUserProfile自動作成）
        import school_diary.diary.signals  # noqa: F401

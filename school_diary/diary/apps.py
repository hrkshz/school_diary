from django.apps import AppConfig


class DiaryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "school_diary.diary"
    verbose_name = "連絡帳"

    def ready(self):
        """アプリ起動時の初期化処理

        全アプリロード完了後に実行される。
        """
        # シグナル登録（User作成時にUserProfile自動作成）
        import school_diary.diary.signals  # noqa: F401

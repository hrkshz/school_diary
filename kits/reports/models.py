"""
レポートシステムのデータモデル

このモジュールは、レポートテンプレート、生成されたレポート、
スケジュール実行の管理を担当します。
"""

import uuid

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class ReportFormat(models.TextChoices):
    """レポートの出力形式"""

    PDF = "pdf", _("PDF")
    CSV = "csv", _("CSV")
    XLSX = "xlsx", _("Excel")
    HTML = "html", _("HTML")


class ReportStatus(models.TextChoices):
    """レポート生成の状態"""

    PENDING = "pending", _("生成待ち")
    GENERATING = "generating", _("生成中")
    COMPLETED = "completed", _("完了")
    FAILED = "failed", _("失敗")


class ChartType(models.TextChoices):
    """グラフの種類"""

    LINE = "line", _("折れ線グラフ")
    BAR = "bar", _("棒グラフ")
    PIE = "pie", _("円グラフ")
    DOUGHNUT = "doughnut", _("ドーナツグラフ")
    RADAR = "radar", _("レーダーチャート")
    SCATTER = "scatter", _("散布図")
    AREA = "area", _("面グラフ")


class ReportTemplate(models.Model):
    """
    レポートテンプレート

    再利用可能なレポートテンプレートを管理します。
    SQLクエリ、グラフ設定、レイアウトを定義できます。
    """

    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("テンプレートコード"),
        help_text=_("システム内で使用する一意の識別子(例: monthly_overtime_report)"),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("テンプレート名"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("説明"),
    )

    # データソース設定
    model_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("モデル名"),
        help_text=_("例: kits.demos.models.OvertimeRequest"),
    )
    query_template = models.TextField(
        blank=True,
        verbose_name=_("クエリテンプレート"),
        help_text=_("Django ORM形式のクエリ(Pythonコード)"),
    )

    # グラフ設定(JSON)
    chart_config = models.JSONField(
        default=dict,
        verbose_name=_("グラフ設定"),
        help_text=_("Chart.js設定(JSON形式)"),
    )

    # 出力設定
    supported_formats = ArrayField(
        models.CharField(max_length=10, choices=ReportFormat.choices),
        default=list,
        verbose_name=_("対応形式"),
    )
    default_format = models.CharField(
        max_length=10,
        choices=ReportFormat.choices,
        default=ReportFormat.PDF,
        verbose_name=_("デフォルト形式"),
    )

    # テンプレートファイル
    html_template = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("HTMLテンプレートパス"),
        help_text=_("例: reports/monthly_overtime.html"),
    )

    # 設定
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("有効"),
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name=_("公開"),
        help_text=_("全ユーザーがアクセス可能か"),
    )

    # メタ情報
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_report_templates",
        verbose_name=_("作成者"),
    )

    class Meta:
        db_table = "kits_report_templates"
        verbose_name = _("レポートテンプレート")
        verbose_name_plural = _("レポートテンプレート")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Report(models.Model):
    """
    生成されたレポート

    個々のレポート生成結果を表します。
    ファイルパス、生成パラメータ、エラー情報などを記録します。
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # テンプレート
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reports",
        verbose_name=_("テンプレート"),
    )

    # 生成者
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="generated_reports",
        verbose_name=_("生成者"),
    )

    # レポート情報
    title = models.CharField(
        max_length=255,
        verbose_name=_("タイトル"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("説明"),
    )

    # 出力形式
    format = models.CharField(
        max_length=10,
        choices=ReportFormat.choices,
        default=ReportFormat.PDF,
        verbose_name=_("形式"),
    )

    # ファイル情報
    file = models.FileField(
        upload_to="reports/%Y/%m/%d/",
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["pdf", "csv", "xlsx", "html"]),
        ],
        verbose_name=_("ファイル"),
    )
    file_size = models.PositiveBigIntegerField(
        default=0,
        verbose_name=_("ファイルサイズ(bytes)"),
    )

    # 生成パラメータ
    parameters = models.JSONField(
        default=dict,
        verbose_name=_("パラメータ"),
        help_text=_("レポート生成時のフィルタ条件など"),
    )

    # ステータス
    status = models.CharField(
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.PENDING,
        verbose_name=_("ステータス"),
    )

    # タイムスタンプ
    generated_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("生成日時"),
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("有効期限"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # エラー情報
    error_message = models.TextField(
        blank=True,
        verbose_name=_("エラーメッセージ"),
    )

    # 統計情報
    row_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("データ行数"),
    )
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("ダウンロード回数"),
    )

    class Meta:
        db_table = "kits_reports"
        verbose_name = _("レポート")
        verbose_name_plural = _("レポート")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["generated_by", "status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_format_display()})"

    def mark_as_completed(self, file_path: str, file_size: int, row_count: int = 0):
        """生成完了としてマーク"""
        self.status = ReportStatus.COMPLETED
        self.file = file_path
        self.file_size = file_size
        self.row_count = row_count
        self.generated_at = timezone.now()
        self.save(
            update_fields=[
                "status",
                "file",
                "file_size",
                "row_count",
                "generated_at",
                "updated_at",
            ],
        )

    def mark_as_failed(self, error_message: str):
        """生成失敗としてマーク"""
        self.status = ReportStatus.FAILED
        self.error_message = error_message
        self.save(update_fields=["status", "error_message", "updated_at"])

    def increment_download_count(self):
        """ダウンロード回数をインクリメント"""
        self.download_count += 1
        self.save(update_fields=["download_count", "updated_at"])

    @property
    def is_expired(self) -> bool:
        """有効期限切れかどうか"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_downloadable(self) -> bool:
        """ダウンロード可能かどうか"""
        return (
            self.status == ReportStatus.COMPLETED
            and bool(self.file)
            and not self.is_expired
        )


class ReportSchedule(models.Model):
    """
    レポートスケジュール

    定期的なレポート生成を設定します。
    週次・月次レポートなど。
    """

    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name="schedules",
        verbose_name=_("テンプレート"),
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_("スケジュール名"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("説明"),
    )

    # Cron形式のスケジュール設定
    cron_expression = models.CharField(
        max_length=100,
        default="0 9 1 * *",  # 毎月1日の9:00AM
        verbose_name=_("Cron式"),
        help_text=_("例: '0 9 * * 1' = 毎週月曜日9:00AM"),
    )

    # パラメータ
    parameters = models.JSONField(
        default=dict,
        verbose_name=_("パラメータ"),
    )

    # 出力形式
    format = models.CharField(
        max_length=10,
        choices=ReportFormat.choices,
        default=ReportFormat.PDF,
        verbose_name=_("形式"),
    )

    # 送信設定
    send_to_users = models.ManyToManyField(
        User,
        blank=True,
        related_name="scheduled_reports",
        verbose_name=_("送信先ユーザー"),
    )
    send_to_emails = ArrayField(
        models.EmailField(),
        default=list,
        blank=True,
        verbose_name=_("送信先メールアドレス"),
    )

    # 設定
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("有効"),
    )

    # タイムスタンプ
    last_run_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("最終実行日時"),
    )
    next_run_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("次回実行予定日時"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "kits_report_schedules"
        verbose_name = _("レポートスケジュール")
        verbose_name_plural = _("レポートスケジュール")
        ordering = ["next_run_at"]

    def __str__(self):
        return f"{self.name} ({self.cron_expression})"

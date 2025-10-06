"""
データI/Oシステムのデータモデル

このモジュールは、インポート履歴、マッピング設定、
エラーログの管理を担当します。
"""

import uuid

from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class ImportStatus(models.TextChoices):
    """インポートの状態"""

    PENDING = "pending", _("処理待ち")
    PROCESSING = "processing", _("処理中")
    COMPLETED = "completed", _("完了")
    FAILED = "failed", _("失敗")
    PARTIAL = "partial", _("一部成功")


class DuplicateStrategy(models.TextChoices):
    """重複時の処理方法"""

    SKIP = "skip", _("スキップ")
    UPDATE = "update", _("更新")
    RENUMBER = "renumber", _("新規採番")
    ERROR = "error", _("エラー")


class ImportMapping(models.Model):
    """
    インポートマッピング設定

    CSVカラムとDjangoモデルフィールドの対応関係を保存します。
    再利用可能なマッピング設定を管理できます。
    """

    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("マッピングコード"),
        help_text=_("システム内で使用する一意の識別子（例: book_import_mapping）"),
    )
    name = models.CharField(
        max_length=200,
        verbose_name=_("マッピング名"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("説明"),
    )

    # 対象モデル
    model_name = models.CharField(
        max_length=200,
        verbose_name=_("モデル名"),
        help_text=_("例: library.Book"),
    )

    # マッピング定義（JSON）
    field_mapping = models.JSONField(
        default=dict,
        verbose_name=_("フィールドマッピング"),
        help_text=_("{'CSVカラム名': 'モデルフィールド名'}"),
    )

    # バリデーション設定
    validation_rules = models.JSONField(
        default=dict,
        verbose_name=_("バリデーションルール"),
        help_text=_("フィールドごとのバリデーション設定"),
    )

    # 重複チェック設定
    unique_fields = models.JSONField(
        default=list,
        verbose_name=_("一意フィールド"),
        help_text=_("重複チェックに使用するフィールドのリスト"),
    )
    duplicate_strategy = models.CharField(
        max_length=20,
        choices=DuplicateStrategy.choices,
        default=DuplicateStrategy.SKIP,
        verbose_name=_("重複時の処理"),
    )

    # 設定
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("有効"),
    )

    # メタ情報
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_import_mappings",
        verbose_name=_("作成者"),
    )

    class Meta:
        db_table = "kits_import_mappings"
        verbose_name = _("インポートマッピング")
        verbose_name_plural = _("インポートマッピング")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class ImportHistory(models.Model):
    """
    インポート履歴

    個々のインポート実行結果を記録します。
    成功件数、失敗件数、エラー内容などを保存します。
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # マッピング
    mapping = models.ForeignKey(
        ImportMapping,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_histories",
        verbose_name=_("マッピング"),
    )

    # 実行者
    imported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="import_histories",
        verbose_name=_("実行者"),
    )

    # ファイル情報
    original_filename = models.CharField(
        max_length=255,
        verbose_name=_("元ファイル名"),
    )
    file = models.FileField(
        upload_to="imports/%Y/%m/%d/",
        blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=["csv", "tsv", "txt", "xlsx", "xls"])
        ],
        verbose_name=_("ファイル"),
    )
    file_size = models.PositiveBigIntegerField(
        default=0,
        verbose_name=_("ファイルサイズ（bytes）"),
    )
    encoding = models.CharField(
        max_length=50,
        default="utf-8",
        verbose_name=_("文字コード"),
    )

    # インポート設定
    model_name = models.CharField(
        max_length=200,
        verbose_name=_("モデル名"),
    )
    parameters = models.JSONField(
        default=dict,
        verbose_name=_("パラメータ"),
        help_text=_("インポート時の設定"),
    )

    # ステータス
    status = models.CharField(
        max_length=20,
        choices=ImportStatus.choices,
        default=ImportStatus.PENDING,
        verbose_name=_("ステータス"),
    )

    # 統計情報
    total_rows = models.PositiveIntegerField(
        default=0,
        verbose_name=_("総行数"),
    )
    success_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("成功件数"),
    )
    failed_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("失敗件数"),
    )
    skipped_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("スキップ件数"),
    )
    updated_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("更新件数"),
    )
    renumbered_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("新規採番件数"),
    )

    # タイムスタンプ
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("開始日時"),
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("完了日時"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # エラー情報
    error_message = models.TextField(
        blank=True,
        verbose_name=_("エラーメッセージ"),
    )
    error_details = models.JSONField(
        default=list,
        verbose_name=_("エラー詳細"),
        help_text=_("各行のエラー情報"),
    )

    class Meta:
        db_table = "kits_import_histories"
        verbose_name = _("インポート履歴")
        verbose_name_plural = _("インポート履歴")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["imported_by", "status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.original_filename} ({self.get_status_display()})"

    def mark_as_processing(self):
        """処理中としてマーク"""
        self.status = ImportStatus.PROCESSING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at", "updated_at"])

    def mark_as_completed(
        self,
        success_count: int,
        failed_count: int = 0,
        skipped_count: int = 0,
        updated_count: int = 0,
        renumbered_count: int = 0,
    ):
        """完了としてマーク"""
        self.status = ImportStatus.COMPLETED if failed_count == 0 else ImportStatus.PARTIAL
        self.success_count = success_count
        self.failed_count = failed_count
        self.skipped_count = skipped_count
        self.updated_count = updated_count
        self.renumbered_count = renumbered_count
        self.completed_at = timezone.now()
        self.save(
            update_fields=[
                "status",
                "success_count",
                "failed_count",
                "skipped_count",
                "updated_count",
                "renumbered_count",
                "completed_at",
                "updated_at",
            ]
        )

    def mark_as_failed(self, error_message: str):
        """失敗としてマーク"""
        self.status = ImportStatus.FAILED
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "error_message", "completed_at", "updated_at"])

    def add_error(self, row_number: int, field: str, error: str):
        """エラーを追加"""
        self.error_details.append(
            {
                "row": row_number,
                "field": field,
                "error": error,
            }
        )
        self.save(update_fields=["error_details", "updated_at"])

    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_rows == 0:
            return 0.0
        return (self.success_count / self.total_rows) * 100

    @property
    def duration(self):
        """処理時間"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None

"""Django管理画面設定"""

import json

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import ImportHistory
from .models import ImportMapping


@admin.register(ImportMapping)
class ImportMappingAdmin(admin.ModelAdmin):
    """インポートマッピング管理画面"""

    list_display = [
        "code",
        "name",
        "model_name",
        "duplicate_strategy",
        "is_active",
        "usage_count",
        "updated_at",
    ]
    list_filter = ["is_active", "duplicate_strategy", "updated_at"]
    search_fields = ["code", "name", "model_name", "description"]
    readonly_fields = ["created_at", "updated_at", "usage_count"]

    fieldsets = (
        (
            "基本情報",
            {
                "fields": ("code", "name", "description", "model_name", "is_active"),
            },
        ),
        (
            "マッピング設定",
            {
                "fields": ("field_mapping", "validation_rules"),
            },
        ),
        (
            "重複処理",
            {
                "fields": ("unique_fields", "duplicate_strategy"),
            },
        ),
        (
            "メタ情報",
            {
                "fields": ("usage_count", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="使用回数")
    def usage_count(self, obj):
        """使用回数を表示"""
        count = obj.import_histories.count()
        url = reverse("admin:io_importhistory_changelist") + f"?mapping__id__exact={obj.id}"
        return format_html('<a href="{}">{} 件</a>', url, count)


@admin.register(ImportHistory)
class ImportHistoryAdmin(admin.ModelAdmin):
    """インポート履歴管理画面"""

    list_display = [
        "id",
        "original_filename",
        "model_name",
        "status_badge",
        "total_rows",
        "success_count",
        "failed_count",
        "success_rate_display",
        "duration_display",
        "imported_by",
        "created_at",
    ]
    list_filter = [
        "status",
        "model_name",
        "created_at",
    ]
    search_fields = [
        "id",
        "original_filename",
        "model_name",
        "imported_by__email",
    ]
    readonly_fields = [
        "id",
        "mapping",
        "imported_by",
        "file",
        "file_size_display",
        "encoding",
        "parameters_display",
        "total_rows",
        "success_count",
        "failed_count",
        "skipped_count",
        "updated_count",
        "renumbered_count",
        "success_rate_display",
        "duration_display",
        "error_details_display",
        "created_at",
        "updated_at",
        "started_at",
        "completed_at",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "基本情報",
            {
                "fields": ("id", "mapping", "model_name", "imported_by"),
            },
        ),
        (
            "ファイル情報",
            {
                "fields": ("original_filename", "file", "file_size_display", "encoding"),
            },
        ),
        (
            "ステータス",
            {
                "fields": ("status", "started_at", "completed_at", "duration_display"),
            },
        ),
        (
            "統計情報",
            {
                "fields": (
                    "total_rows",
                    "success_count",
                    "failed_count",
                    "skipped_count",
                    "updated_count",
                    "renumbered_count",
                    "success_rate_display",
                ),
            },
        ),
        (
            "エラー情報",
            {
                "fields": ("error_message", "error_details_display"),
                "classes": ("collapse",),
            },
        ),
        (
            "パラメータ",
            {
                "fields": ("parameters_display",),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="ステータス")
    def status_badge(self, obj):
        """ステータスをバッジ表示"""
        colors = {
            "pending": "gray",
            "processing": "blue",
            "completed": "green",
            "failed": "red",
            "partial": "orange",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description="ファイルサイズ")
    def file_size_display(self, obj):
        """ファイルサイズを人間が読める形式で表示"""
        size = obj.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @admin.display(description="成功率")
    def success_rate_display(self, obj):
        """成功率を表示"""
        return f"{obj.success_rate:.1f}%"

    @admin.display(description="処理時間")
    def duration_display(self, obj):
        """処理時間を表示"""
        duration = obj.duration
        if duration:
            total_seconds = int(duration.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            return f"{minutes}分{seconds}秒"
        return "-"

    @admin.display(description="パラメータ")
    def parameters_display(self, obj):
        """パラメータを整形表示"""
        return mark_safe(f"<pre>{json.dumps(obj.parameters, indent=2, ensure_ascii=False)}</pre>")

    @admin.display(description="エラー詳細")
    def error_details_display(self, obj):
        """エラー詳細を整形表示"""
        if obj.error_details:
            return mark_safe(
                f"<pre>{json.dumps(obj.error_details, indent=2, ensure_ascii=False)}</pre>",
            )
        return "-"

"""
Django管理画面設定
"""

import json
from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Report
from .models import ReportSchedule
from .models import ReportTemplate


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """レポートテンプレート管理画面"""

    list_display = [
        "code",
        "name",
        "formats_display",
        "is_active",
        "is_public",
        "usage_count_display",
        "updated_at",
    ]
    list_filter = ["is_active", "is_public", "default_format", "updated_at"]
    search_fields = ["code", "name", "description"]
    readonly_fields = ["created_at", "updated_at", "usage_count_display"]

    fieldsets = (
        (
            "基本情報",
            {
                "fields": ("code", "name", "description", "is_active", "is_public"),
            },
        ),
        (
            "データソース",
            {
                "fields": ("model_name", "query_template"),
            },
        ),
        (
            "出力設定",
            {
                "fields": ("supported_formats", "default_format", "html_template"),
            },
        ),
        (
            "グラフ設定",
            {
                "fields": ("chart_config",),
            },
        ),
        (
            "メタ情報",
            {
                "fields": ("usage_count_display", "created_by", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="対応形式")
    def formats_display(self, obj):
        """対応形式を表示"""
        return ", ".join(obj.supported_formats)

    @admin.display(description="使用回数")
    def usage_count_display(self, obj):
        """使用回数を表示"""
        count = obj.reports.count()
        url = reverse("admin:reports_report_changelist") + f"?template__id__exact={obj.id}"
        return format_html('<a href="{}">{} 件</a>', url, count)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """レポート管理画面"""

    list_display = [
        "id",
        "title",
        "template",
        "format",
        "status_badge",
        "generated_by",
        "file_size_display",
        "row_count",
        "download_count",
        "generated_at",
    ]
    list_filter = [
        "format",
        "status",
        "generated_at",
        "created_at",
    ]
    search_fields = [
        "id",
        "title",
        "generated_by__email",
        "generated_by__name",
    ]
    readonly_fields = [
        "id",
        "template",
        "generated_by",
        "file",
        "file_size_display",
        "parameters_display",
        "created_at",
        "updated_at",
        "generated_at",
        "download_count",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "基本情報",
            {
                "fields": ("id", "template", "title", "description", "generated_by"),
            },
        ),
        (
            "ファイル情報",
            {
                "fields": ("format", "file", "file_size_display", "row_count"),
            },
        ),
        (
            "ステータス",
            {
                "fields": ("status", "generated_at", "expires_at", "error_message"),
            },
        ),
        (
            "統計情報",
            {
                "fields": ("download_count", "parameters_display"),
            },
        ),
        (
            "メタ情報",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["cleanup_files"]

    @admin.display(description="ステータス")
    def status_badge(self, obj):
        """ステータスをバッジ表示"""
        colors = {
            "pending": "gray",
            "generating": "blue",
            "completed": "green",
            "failed": "red",
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

    @admin.display(description="パラメータ")
    def parameters_display(self, obj):
        """パラメータを整形表示"""
        return mark_safe(f"<pre>{json.dumps(obj.parameters, indent=2, ensure_ascii=False)}</pre>")

    @admin.action(description="選択したレポートのファイルを削除")
    def cleanup_files(self, request, queryset):
        """選択したレポートのファイルを削除"""
        count = 0
        for report in queryset:
            if report.file:
                file_path = Path(settings.MEDIA_ROOT) / report.file.name
                if file_path.exists():
                    file_path.unlink()
                    count += 1

        self.message_user(request, f"{count}件のファイルを削除しました。")


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    """レポートスケジュール管理画面"""

    list_display = [
        "name",
        "template",
        "cron_expression",
        "format",
        "is_active",
        "last_run_at",
        "next_run_at",
    ]
    list_filter = ["is_active", "format", "template"]
    search_fields = ["name", "description"]
    filter_horizontal = ["send_to_users"]

    fieldsets = (
        (
            "基本情報",
            {
                "fields": ("name", "description", "template", "is_active"),
            },
        ),
        (
            "スケジュール設定",
            {
                "fields": ("cron_expression", "parameters", "format"),
            },
        ),
        (
            "送信設定",
            {
                "fields": ("send_to_users", "send_to_emails"),
            },
        ),
        (
            "実行履歴",
            {
                "fields": ("last_run_at", "next_run_at"),
                "classes": ("collapse",),
            },
        ),
    )

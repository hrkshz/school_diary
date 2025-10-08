from django.contrib import admin
from django.contrib import messages
from django.utils import timezone
from django.utils.html import format_html

from .models import ClassRoom
from .models import DiaryEntry
from .models import TeacherNote


@admin.register(DiaryEntry)
class DiaryEntryAdmin(admin.ModelAdmin):
    """連絡帳エントリーの管理画面"""

    list_display = (
        "student",
        "entry_date",
        "health_display",
        "mental_display",
        "is_read",
        "read_by",
        "submission_date",
    )
    list_filter = ("is_read", "entry_date", "health_condition", "mental_condition")
    search_fields = (
        "student__username",
        "student__first_name",
        "student__last_name",
        "reflection",
    )
    readonly_fields = ("submission_date", "read_at")
    date_hierarchy = "entry_date"
    actions = ["mark_as_read_bulk"]

    fieldsets = (
        (
            "基本情報",
            {
                "fields": ("student", "entry_date", "submission_date"),
            },
        ),
        (
            "体調・メンタル",
            {
                "fields": ("health_condition", "mental_condition"),
            },
        ),
        (
            "振り返り",
            {
                "fields": ("reflection",),
            },
        ),
        (
            "既読情報",
            {
                "fields": ("is_read", "read_by", "read_at"),
            },
        ),
    )

    @admin.display(description='体調')
    def health_display(self, obj):
        """体調を色分けして表示"""
        colors = {1: 'red', 2: 'orange', 3: 'gray', 4: 'lightgreen', 5: 'green'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.health_condition, 'black'),
            obj.get_health_condition_display()
        )

    @admin.display(description='メンタル')
    def mental_display(self, obj):
        """メンタルを色分けして表示"""
        colors = {1: 'red', 2: 'orange', 3: 'gray', 4: 'lightgreen', 5: 'green'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.mental_condition, 'black'),
            obj.get_mental_condition_display()
        )

    @admin.action(description="選択した連絡帳を既読にする")
    def mark_as_read_bulk(self, request, queryset):
        """選択された未読の連絡帳を一括で既読にする"""
        unread = queryset.filter(is_read=False)
        count = unread.count()

        if count == 0:
            self.message_user(
                request,
                "既読にする項目がありません(全て既読済み)。",
                messages.WARNING,
            )
            return

        unread.update(
            is_read=True,
            read_by=request.user,
            read_at=timezone.now(),
        )
        self.message_user(
            request,
            f"{count}件を既読にしました。",
            messages.SUCCESS,
        )


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    """クラスの管理画面"""

    list_display = (
        "__str__",
        "grade",
        "class_name",
        "academic_year",
        "homeroom_teacher",
        "student_count",
    )
    list_filter = ("academic_year", "grade", "class_name")
    search_fields = (
        "homeroom_teacher__username",
        "homeroom_teacher__first_name",
        "homeroom_teacher__last_name",
    )
    filter_horizontal = ("students",)

    fieldsets = (
        (
            "クラス情報",
            {
                "fields": ("grade", "class_name", "academic_year"),
            },
        ),
        (
            "担任・生徒",
            {
                "fields": ("homeroom_teacher", "students"),
            },
        ),
    )


@admin.register(TeacherNote)
class TeacherNoteAdmin(admin.ModelAdmin):
    """担任メモの管理画面"""

    list_display = ("teacher", "diary_entry", "is_shared", "created_at")
    list_filter = ("is_shared", "created_at")
    search_fields = (
        "teacher__username",
        "teacher__first_name",
        "teacher__last_name",
        "diary_entry__student__username",
        "note",
    )
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "基本情報",
            {
                "fields": ("diary_entry", "teacher", "created_at"),
            },
        ),
        (
            "メモ内容",
            {
                "fields": ("note", "is_shared"),
            },
        ),
    )

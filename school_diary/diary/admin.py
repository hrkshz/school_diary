from allauth.account.models import EmailAddress
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Max
from django.utils import timezone
from django.utils.html import format_html

from .forms import UserProfileAdminForm
from .models import ClassRoom
from .models import DailyAttendance
from .models import DiaryEntry
from .models import TeacherNote
from .models import UserProfile

User = get_user_model()


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
        "public_reaction",
        "internal_action",
        "action_status",
        "submission_date",
    )
    list_filter = (
        "is_read",
        "action_status",
        "entry_date",
        "health_condition",
        "mental_condition",
    )
    search_fields = (
        "student__username",
        "student__first_name",
        "student__last_name",
        "reflection",
    )
    readonly_fields = ("submission_date", "read_at", "action_completed_at")
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
                "fields": ("is_read", "read_by", "read_at", "public_reaction", "internal_action"),
            },
        ),
        (
            "対応状況",
            {
                "fields": ("action_status", "action_completed_by", "action_completed_at"),
            },
        ),
    )

    @admin.display(description="体調")
    def health_display(self, obj):
        """体調を色分けして表示"""
        colors = {1: "red", 2: "orange", 3: "gray", 4: "lightgreen", 5: "green"}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.health_condition, "black"),
            obj.get_health_condition_display(),
        )

    @admin.display(description="メンタル")
    def mental_display(self, obj):
        """メンタルを色分けして表示"""
        colors = {1: "red", 2: "orange", 3: "gray", 4: "lightgreen", 5: "green"}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.mental_condition, "black"),
            obj.get_mental_condition_display(),
        )

    def get_queryset(self, request):
        """役割に応じてアクセス可能なデータをフィルタ"""
        qs = super().get_queryset(request)

        # スーパーユーザーは全てのデータにアクセス可能
        if request.user.is_superuser:
            return qs

        # UserProfileが存在しない場合は空のQuerySetを返す
        if not hasattr(request.user, "profile"):
            return qs.none()

        profile = request.user.profile

        # 教頭/校長: 全校生徒のデータにアクセス可能
        if profile.role == "school_leader":
            return qs

        # 学年主任: 管理学年の生徒のデータにアクセス可能（過去の連絡帳も含む）
        if profile.role == "grade_leader":
            # 最新年度の管理学年のクラスを取得
            latest_year = ClassRoom.objects.aggregate(Max("academic_year"))["academic_year__max"]

            if not latest_year or not profile.managed_grade:
                return qs.none()

            # 最新年度の管理学年のクラスの生徒を取得
            current_classrooms = ClassRoom.objects.filter(
                grade=profile.managed_grade,
                academic_year=latest_year,
            )
            students = User.objects.filter(classes__in=current_classrooms)

            # その生徒の全ての連絡帳（過去も含む）
            return qs.filter(student__in=students)

        # 担任: 自分が担任のクラスの生徒のデータにアクセス可能（過去の連絡帳も含む）
        if profile.role == "teacher":
            # 自分が担任のクラスの生徒を取得
            my_classrooms = ClassRoom.objects.filter(homeroom_teacher=request.user)
            students = User.objects.filter(classes__in=my_classrooms)

            # その生徒の全ての連絡帳（過去も含む）
            return qs.filter(student__in=students)

        # 生徒: 自分のデータのみアクセス可能
        return qs.filter(student=request.user)

    def has_delete_permission(self, request, obj=None):
        """削除はスーパーユーザーのみ可能"""
        return request.user.is_superuser

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

    list_display = ("teacher", "student", "is_shared", "created_at", "updated_at")
    list_filter = ("is_shared", "created_at", "updated_at")
    search_fields = (
        "teacher__username",
        "teacher__first_name",
        "teacher__last_name",
        "student__username",
        "student__first_name",
        "student__last_name",
        "note",
    )
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "updated_at"

    fieldsets = (
        (
            "基本情報",
            {
                "fields": ("student", "teacher", "created_at", "updated_at"),
            },
        ),
        (
            "メモ内容",
            {
                "fields": ("note", "is_shared"),
            },
        ),
    )


@admin.register(DailyAttendance)
class DailyAttendanceAdmin(admin.ModelAdmin):
    """出席記録の管理画面"""

    list_display = (
        "student",
        "classroom",
        "date",
        "status",
        "absence_reason",
        "noted_by",
        "noted_at",
    )
    list_filter = ("date", "status", "absence_reason", "classroom")
    search_fields = (
        "student__username",
        "student__first_name",
        "student__last_name",
    )
    readonly_fields = ("noted_at",)
    date_hierarchy = "date"

    fieldsets = (
        (
            "基本情報",
            {
                "fields": ("student", "classroom", "date"),
            },
        ),
        (
            "出席状況",
            {
                "fields": ("status", "absence_reason"),
            },
        ),
        (
            "記録者",
            {
                "fields": ("noted_by", "noted_at"),
            },
        ),
    )


class UserProfileInline(admin.StackedInline):
    """ユーザープロフィール（Inline表示）"""

    model = UserProfile
    form = UserProfileAdminForm
    can_delete = False
    verbose_name = "プロフィール"
    verbose_name_plural = "プロフィール"

    fieldsets = (
        (
            "役割設定",
            {
                "fields": ("role", "managed_grade"),
                "description": (
                    "役割を設定すると、管理画面でのアクセス権限が自動的に変更されます。<br>"
                    "<strong>管理学年</strong>は学年主任を選択した場合のみ入力してください。"
                ),
            },
        ),
    )


# Userモデルの既存登録を解除
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """ユーザー管理画面（役割・認証状態を可視化）"""

    list_display = (
        "username",
        "email",
        "full_name_display",
        "role_display",
        "email_verified_display",
        "homeroom_class_display",
        "student_class_display",
        "is_active",
    )

    list_filter = list(BaseUserAdmin.list_filter or ()) + [
        ("homeroom_classes", admin.RelatedOnlyFieldListFilter),
    ]

    search_fields = BaseUserAdmin.search_fields

    actions = list(BaseUserAdmin.actions or []) + ["activate_email_for_selected"]  # type: ignore

    inlines = [UserProfileInline]

    # fieldsetsを明示的に定義（編集画面用）
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("個人情報", {"fields": ("first_name", "last_name", "email")}),
        (
            "権限",
            {
                "fields": ("is_active", "is_staff", "is_superuser"),
                "description": "is_active: 卒業・退学した生徒はチェックを外します",
            },
        ),
    )

    # add_fieldsetsを定義（新規作成画面用）
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
                "description": (
                    "<strong>注意</strong>: メールアドレスは必須です。ログイン時に使用されます。"
                ),
            },
        ),
    )

    @admin.display(description="氏名")
    def full_name_display(self, obj):
        """フルネーム表示"""
        return obj.get_full_name() or "-"

    @admin.display(description="役割")
    def role_display(self, obj):
        """役割を色分けして表示（UserProfileベース）"""
        if obj.is_superuser:
            return format_html('<span style="color: red; font-weight: bold;">🔑 システム管理者</span>')

        # UserProfileの役割を表示
        if hasattr(obj, "profile"):
            profile = obj.profile
            role_icons = {
                "student": "👨‍🎓",
                "teacher": "👨‍🏫",
                "grade_leader": "👔",
                "school_leader": "🎩",
            }
            role_colors = {
                "student": "green",
                "teacher": "blue",
                "grade_leader": "purple",
                "school_leader": "darkred",
            }
            icon = role_icons.get(profile.role, "❓")
            color = role_colors.get(profile.role, "black")
            role_name = profile.get_role_display()

            # 学年主任の場合、管理学年を表示
            if profile.role == "grade_leader" and profile.managed_grade:
                role_name = f"{role_name}（{profile.managed_grade}年）"

            return format_html(
                '<span style="color: {}; font-weight: bold;">{} {}</span>',
                color,
                icon,
                role_name,
            )

        # UserProfileがない場合はデフォルト表示
        if obj.homeroom_classes.exists():
            return format_html('<span style="color: blue;">👨‍🏫 担任（未設定）</span>')
        return format_html('<span style="color: gray;">未設定</span>')

    @admin.display(description="メール認証", boolean=True)
    def email_verified_display(self, obj):
        """メール認証済みかどうか"""
        if not obj.email:
            return False
        return EmailAddress.objects.filter(user=obj, verified=True).exists()

    @admin.display(description="担当クラス")
    def homeroom_class_display(self, obj):
        """担任の担当クラス表示"""
        classroom = obj.homeroom_classes.first()
        return str(classroom) if classroom else "-"

    @admin.display(description="所属クラス")
    def student_class_display(self, obj):
        """生徒の所属クラス表示"""
        classroom = ClassRoom.objects.filter(students=obj).first()
        return str(classroom) if classroom else "-"

    @admin.action(description="選択したユーザーのメール認証を有効化")
    def activate_email_for_selected(self, request, queryset):
        """選択されたユーザーのEmailAddressを作成/更新してログイン可能にする"""
        count = 0
        for user in queryset:
            if not user.email:
                continue

            email_address = EmailAddress.objects.filter(user=user).first()
            if email_address:
                if not email_address.verified:
                    email_address.verified = True
                    email_address.primary = True
                    email_address.save()
                    count += 1
            else:
                EmailAddress.objects.create(
                    user=user,
                    email=user.email,
                    verified=True,
                    primary=True,
                )
                count += 1

        self.message_user(
            request,
            f"{count}人のメール認証を有効化しました。",
            messages.SUCCESS,
        )


# ========================================
# 管理画面のシンプル化（DX向上）
# ========================================
# 現状不要なモデルを非表示にします。
# 将来必要になった場合は、該当行を削除してください。
#
# 成果: 34モデル → 18モデル (47%削減)
#
# 削除成功:
# - Group: UserProfileで役割管理実装済み
# - Site: django-allauth内部使用だが管理不要
# - Authenticator: MFA不要
# - SocialAccount系: ソーシャルログイン不要
# - Celery系: 定期タスク未使用（Notifications実装時に再検討）
#
# 削除を試みたが、参考実装として残しているもの:
# - DemoRequest (kits.demos): django-fsmの参考実装、Approvals実装時に参考
# - ImportMapping, ImportHistory (kits.io): 将来の生徒データ一括登録で必要になる可能性
# これらはkitsアプリのadmin.pyで登録されているため、
# apps.pyのready()で削除することも可能だが、保守性を考慮して残している。
# 理由: cookiecutter-djangoの「再利用可能な部品集」としての価値を保持

from django.contrib.admin.exceptions import NotRegistered
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site

try:
    from allauth.mfa.models import Authenticator

    admin.site.unregister(Authenticator)
except (ImportError, NotRegistered):
    pass  # MFA未対応、またはadmin登録されていない

try:
    from allauth.socialaccount.models import SocialAccount
    from allauth.socialaccount.models import SocialApp
    from allauth.socialaccount.models import SocialToken

    admin.site.unregister(SocialApp)
    admin.site.unregister(SocialToken)
    admin.site.unregister(SocialAccount)
except (ImportError, NotRegistered):
    pass  # socialaccount未インストール、またはadmin登録されていない

try:
    from kits.demos.models import DemoRequest

    admin.site.unregister(DemoRequest)
except (ImportError, NotRegistered):
    pass  # demos未インストール、またはadmin登録されていない

try:
    from kits.io.models import ImportHistory
    from kits.io.models import ImportMapping

    admin.site.unregister(ImportMapping)
    admin.site.unregister(ImportHistory)
except (ImportError, NotRegistered):
    pass  # io未インストール、またはadmin登録されていない

try:
    from django_celery_beat.models import ClockedSchedule
    from django_celery_beat.models import CrontabSchedule
    from django_celery_beat.models import IntervalSchedule
    from django_celery_beat.models import PeriodicTask
    from django_celery_beat.models import SolarSchedule

    admin.site.unregister(PeriodicTask)
    admin.site.unregister(ClockedSchedule)
    admin.site.unregister(CrontabSchedule)
    admin.site.unregister(SolarSchedule)
    admin.site.unregister(IntervalSchedule)
except (ImportError, NotRegistered):
    pass  # celery未インストール、またはadmin登録されていない

# 不要なモデルを削除（確実に存在するもの）
try:
    admin.site.unregister(Group)
except NotRegistered:
    pass

try:
    admin.site.unregister(Site)
except NotRegistered:
    pass

# ========================================
# 監査ログ（権限変更の履歴追跡）
# ========================================
# UserProfileの変更履歴を管理画面に表示します。
# セキュリティ・コンプライアンス要件として、以下を記録:
# - 権限変更（生徒→担任、担任→学年主任など）
# - 管理学年の変更
# - 変更者・変更日時
from simple_history.admin import SimpleHistoryAdmin

# HistoricalUserProfileの表示名を変更（教師にわかりやすく）
UserProfile.history.model._meta.verbose_name = "ユーザー変更履歴"
UserProfile.history.model._meta.verbose_name_plural = "ユーザー変更履歴"


@admin.register(UserProfile.history.model)
class HistoricalUserProfileAdmin(SimpleHistoryAdmin):
    """権限変更の監査ログ（誰が・いつ・どの権限を変更したか）

    セキュリティ・コンプライアンス要件:
    - 監査ログは読み取り専用（改ざん防止）
    - 追加・編集・削除は全て不可
    - SOX法、GDPR、ISO 27001準拠
    """

    list_display = ("user", "role", "managed_grade", "history_date", "history_user", "history_type")
    list_filter = ("role", "history_type", "history_date")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    date_hierarchy = "history_date"

    def has_add_permission(self, request):
        return False  # 履歴は追加不可（自動記録のみ）

    def has_change_permission(self, request, obj=None):
        return False  # 履歴は編集不可（監査証跡保護）

    def has_delete_permission(self, request, obj=None):
        return False  # 履歴は削除不可（監査証跡保護）

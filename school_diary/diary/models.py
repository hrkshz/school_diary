from django.conf import settings
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from .constants import GRADE_CHOICES
from .constants import ConditionLevel


class TeacherReaction(models.TextChoices):
    """担任の対応アクション（非推奨: public_reaction と internal_action を使用）"""

    ENCOURAGE = "encourage", "👍 励まし"
    COMMENTED = "commented", "💬 コメント済み"
    NEEDS_FOLLOW_UP = "needs_follow_up", "⚠️ 要フォロー"
    CONFIRMED = "confirmed", "✅ 確認済み"
    PARENT_CONTACTED = "parent_contacted", "📞 保護者連絡済み"


class PublicReaction(models.TextChoices):
    """生徒に見える反応（ポジティブフィードバック）"""

    THUMBS_UP = "thumbs_up", "👍 いいね"
    WELL_DONE = "well_done", "💯 よくできました"
    GOOD_EFFORT = "good_effort", "💪 がんばったね"
    EXCELLENT = "excellent", "🌟 素晴らしい"
    SUPPORT = "support", "❤️ 応援してるよ"
    CHECKED = "checked", "📖 読んだよ"


class InternalAction(models.TextChoices):
    """先生だけが見る対応記録（内部管理）"""

    NEEDS_FOLLOW_UP = "needs_follow_up", "⚠️ 要フォロー"
    URGENT = "urgent", "🔴 緊急対応必要"
    PARENT_CONTACTED = "parent_contacted", "📞 保護者連絡"
    INDIVIDUAL_TALK = "individual_talk", "🗣️ 個別面談"
    SHARED_MEETING = "shared_meeting", "👥 学年共有"
    MONITORING = "monitoring", "📝 継続観察"


class ActionStatus(models.TextChoices):
    """対応状況（internal_actionの状態管理）"""

    PENDING = "pending", "未対応"
    IN_PROGRESS = "in_progress", "対応中"
    COMPLETED = "completed", "対応済み"
    NOT_REQUIRED = "not_required", "対応不要"


class DiaryEntryQuerySet(models.QuerySet):
    """DiaryEntry用のQuerySet"""

    def with_related(self):
        """関連オブジェクトをprefetch（N+1クエリ解消）"""
        return self.select_related("student", "classroom", "read_by", "action_completed_by")


class DiaryEntryManager(models.Manager):
    """DiaryEntry用のカスタムManager"""

    def get_queryset(self):
        return DiaryEntryQuerySet(self.model, using=self._db)

    def with_related(self):
        return self.get_queryset().with_related()


class DiaryEntry(models.Model):
    """連絡帳エントリー"""

    # カスタムManager
    objects = DiaryEntryManager()

    # 体調・メンタルの選択肢
    CONDITION_CHOICES = [
        (ConditionLevel.VERY_BAD, "とても悪い"),
        (ConditionLevel.BAD, "悪い"),
        (ConditionLevel.NORMAL, "普通"),
        (ConditionLevel.GOOD, "良い"),
        (ConditionLevel.VERY_GOOD, "とても良い"),
    ]

    MENTAL_CHOICES = [
        (ConditionLevel.VERY_BAD, "とても落ち込んでいる"),
        (ConditionLevel.BAD, "落ち込んでいる"),
        (ConditionLevel.NORMAL, "普通"),
        (ConditionLevel.GOOD, "元気"),
        (ConditionLevel.VERY_GOOD, "とても元気"),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="diary_entries",
        verbose_name="生徒",
    )
    classroom = models.ForeignKey(
        "ClassRoom",
        on_delete=models.PROTECT,
        related_name="diary_entries",
        null=True,
        blank=True,
        verbose_name="所属クラス",
        help_text="記載時の所属クラス（年度・学年・組）",
    )
    entry_date = models.DateField(
        "記載日",
        help_text="前登校日の日付",
    )
    submission_date = models.DateTimeField(
        "提出日時",
        default=timezone.now,
    )

    health_condition = models.IntegerField(
        "体調",
        choices=CONDITION_CHOICES,
        default=ConditionLevel.NORMAL,
    )
    mental_condition = models.IntegerField(
        "メンタル",
        choices=MENTAL_CHOICES,
        default=ConditionLevel.NORMAL,
    )
    reflection = models.TextField(
        "今日の振り返り",
        help_text="今日あったこと、学んだこと、感じたことなど",
    )

    is_read = models.BooleanField(
        "既読",
        default=False,
    )
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="read_diary_entries",
        null=True,
        blank=True,
        verbose_name="既読者(担任)",
    )
    read_at = models.DateTimeField(
        "既読日時",
        null=True,
        blank=True,
    )
    teacher_reaction = models.CharField(
        "担任の対応（非推奨）",
        max_length=20,
        choices=TeacherReaction.choices,
        blank=True,
        null=True,
        help_text="非推奨: public_reaction と internal_action を使用",
    )
    public_reaction = models.CharField(
        "生徒への反応",
        max_length=20,
        choices=PublicReaction.choices,
        blank=True,
        null=True,
        help_text="生徒に表示されるポジティブな反応",
    )
    internal_action = models.CharField(
        "対応記録",
        max_length=20,
        choices=InternalAction.choices,
        blank=True,
        null=True,
        help_text="先生のみが見る対応状況（生徒には非表示）",
    )
    action_status = models.CharField(
        "対応状況",
        max_length=20,
        choices=ActionStatus.choices,
        default=ActionStatus.PENDING,
        help_text="internal_actionの対応状況を管理",
    )
    action_completed_at = models.DateTimeField(
        "対応完了日時",
        null=True,
        blank=True,
        help_text="対応完了にした日時",
    )
    action_completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="completed_diary_actions",
        null=True,
        blank=True,
        verbose_name="対応者",
        help_text="対応完了にした担任",
    )
    action_note = models.CharField(
        "対応内容メモ",
        max_length=200,
        blank=True,
        null=True,
        help_text="どのように対応したかを簡潔に記録（引継ぎ・保護者面談で活用）",
    )

    class Meta:
        verbose_name = "連絡帳エントリー"
        verbose_name_plural = "連絡帳エントリー"
        unique_together = ["student", "entry_date"]
        ordering = ["-entry_date", "student__last_name", "student__first_name"]
        indexes = [
            models.Index(fields=["entry_date"]),
            models.Index(fields=["is_read"]),
            models.Index(fields=["action_status"]),
            models.Index(fields=["internal_action"]),
        ]

    def __str__(self):
        student_name = self.student.get_full_name() or self.student.username
        return f"{student_name} - {self.entry_date}"

    def clean(self):
        """バリデーション"""
        from django.core.exceptions import ValidationError

        # 対応完了の場合は対応日時・対応者必須
        if self.action_status == ActionStatus.COMPLETED:
            if not self.action_completed_at:
                raise ValidationError(
                    {
                        "action_completed_at": "対応完了の場合は対応完了日時が必要です",
                    },
                )
            if not self.action_completed_by:
                raise ValidationError(
                    {
                        "action_completed_by": "対応完了の場合は対応者が必要です",
                    },
                )

    def save(self, *args, **kwargs):
        """保存処理

        Note:
            ビジネスロジックはDiaryEntryServiceに移動済み。
            新規作成・更新時はDiaryEntryService.create_entry() / update_entry()を使用してください。
        """
        super().save(*args, **kwargs)

    def mark_as_read(self, teacher):
        """既読処理(イイネスタンプ) - DiaryEntryServiceに委譲"""
        from .services.diary_entry_service import DiaryEntryService

        DiaryEntryService.mark_as_read(self, teacher)

    def mark_action_completed(self, teacher, note=""):
        """対応完了処理 - DiaryEntryServiceに委譲"""
        from .services.diary_entry_service import DiaryEntryService

        DiaryEntryService.mark_action_completed(self, teacher, note=note)

    @property
    def is_editable(self):
        """編集可能かどうか(既読前のみ編集可)"""
        return not self.is_read


class ClassRoomQuerySet(models.QuerySet):
    """ClassRoom用のQuerySet"""

    def with_related(self):
        """関連オブジェクトをprefetch（N+1クエリ解消）"""
        return self.select_related("homeroom_teacher").prefetch_related("assistant_teachers")


class ClassRoomManager(models.Manager):
    """ClassRoom用のカスタムManager"""

    def get_queryset(self):
        return ClassRoomQuerySet(self.model, using=self._db)

    def with_related(self):
        return self.get_queryset().with_related()


class ClassRoom(models.Model):
    """クラス情報"""

    # カスタムManager
    objects = ClassRoomManager()

    CLASS_NAME_CHOICES = [
        ("A", "A組"),
        ("B", "B組"),
        ("C", "C組"),
    ]

    grade = models.IntegerField(
        "学年",
        choices=GRADE_CHOICES,
    )
    class_name = models.CharField(
        "クラス名",
        max_length=10,
        choices=CLASS_NAME_CHOICES,
    )
    academic_year = models.IntegerField(
        "年度",
        default=2025,
    )
    homeroom_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="homeroom_classes",
        null=True,
        blank=True,
        verbose_name="主担任",
    )
    assistant_teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="assistant_classes",
        verbose_name="副担任",
        blank=True,
        help_text="副担任や学年主任など、このクラスの連絡帳を閲覧できる先生を設定",
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="classes",
        verbose_name="生徒",
        blank=True,
    )

    class Meta:
        verbose_name = "クラス"
        verbose_name_plural = "クラス"
        unique_together = ["grade", "class_name", "academic_year"]
        ordering = ["academic_year", "grade", "class_name"]

    def __str__(self):
        year = self.academic_year
        grade = self.get_grade_display()
        class_name = self.get_class_name_display()
        return f"{year}年度 {grade}{class_name}"

    @property
    def student_count(self):
        """生徒数を返す"""
        return self.students.count()

    @property
    def all_teachers(self):
        """主担任と副担任の全リストを返す"""
        teachers = []
        if self.homeroom_teacher:
            teachers.append(self.homeroom_teacher)
        teachers.extend(self.assistant_teachers.all())
        return teachers

    def is_teacher_of_class(self, user):
        """指定ユーザーがこのクラスの担任（主or副）かチェック"""
        if self.homeroom_teacher == user:
            return True
        return self.assistant_teachers.filter(id=user.id).exists()


class UserProfile(models.Model):
    """ユーザープロフィール（役割ベースの権限管理、変更履歴を自動記録）"""

    history = HistoricalRecords()

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="ユーザー",
    )

    ROLE_CHOICES = [
        ("admin", "システム管理者"),
        ("student", "生徒"),
        ("teacher", "担任"),
        ("grade_leader", "学年主任"),
        ("school_leader", "教頭/校長"),
    ]

    # ロール定数（マジックストリング解消）
    ROLE_ADMIN = "admin"
    ROLE_STUDENT = "student"
    ROLE_TEACHER = "teacher"
    ROLE_GRADE_LEADER = "grade_leader"
    ROLE_SCHOOL_LEADER = "school_leader"

    # 担任権限を持つロール（admin.pyでも使用）
    TEACHER_ROLES = [ROLE_TEACHER, ROLE_GRADE_LEADER, ROLE_SCHOOL_LEADER]

    role = models.CharField(
        "役割",
        max_length=20,
        choices=ROLE_CHOICES,
        default="student",
        help_text="ユーザーの役割（アクセス権限を自動的に設定）",
    )
    managed_grade = models.IntegerField(
        "管理学年",
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="学年主任の場合、管理する学年（1, 2, 3）",
    )
    requires_password_change = models.BooleanField(
        "パスワード変更が必要",
        default=False,
        help_text="初回ログイン時にパスワード変更を強制します（管理者が仮パスワードで作成した場合）",
    )

    class Meta:
        verbose_name = "ユーザープロフィール"
        verbose_name_plural = "ユーザープロフィール"

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    def clean(self):
        """バリデーション"""
        from django.core.exceptions import ValidationError

        # 学年主任の場合は管理学年必須
        if self.role == self.ROLE_GRADE_LEADER and not self.managed_grade:
            raise ValidationError(
                {
                    "managed_grade": "学年主任の場合は管理学年を選択してください",
                },
            )

        # 学年主任以外の場合は管理学年不要
        if self.role != self.ROLE_GRADE_LEADER and self.managed_grade:
            raise ValidationError(
                {
                    "managed_grade": "学年主任以外の場合は管理学年を選択しないでください",
                },
            )


class TeacherNoteQuerySet(models.QuerySet):
    """TeacherNote用のQuerySet"""

    def with_related(self):
        """関連オブジェクトをprefetch（N+1クエリ解消）"""
        return self.select_related("teacher", "student")


class TeacherNoteManager(models.Manager):
    """TeacherNote用のカスタムManager"""

    def get_queryset(self):
        return TeacherNoteQuerySet(self.model, using=self._db)

    def with_related(self):
        return self.get_queryset().with_related()


class TeacherNote(models.Model):
    """担任メモ（生徒の長期的な観察記録・引継ぎ情報）"""

    # カスタムManager
    objects = TeacherNoteManager()

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_teacher_notes",
        verbose_name="担任",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_notes_about_me",
        verbose_name="対象生徒",
    )
    note = models.TextField(
        "メモ内容",
        help_text="家庭環境、健康情報、配慮事項など（長期的な観察記録）",
    )
    is_shared = models.BooleanField(
        "学年会議で共有",
        default=False,
        help_text="学年の担任全員が閲覧できます",
    )
    created_at = models.DateTimeField(
        "作成日時",
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        "更新日時",
        auto_now=True,
    )

    class Meta:
        verbose_name = "担任メモ"
        verbose_name_plural = "担任メモ"
        ordering = ["-updated_at"]

    def __str__(self):
        teacher_name = self.teacher.get_full_name() or self.teacher.username
        student_name = self.student.get_full_name() or self.student.username
        return f"{teacher_name} → {student_name}"


class TeacherNoteReadStatusQuerySet(models.QuerySet):
    """TeacherNoteReadStatus用のQuerySet"""

    def with_related(self):
        """関連オブジェクトをprefetch（N+1クエリ解消）"""
        return self.select_related("teacher", "note", "note__teacher", "note__student")


class TeacherNoteReadStatusManager(models.Manager):
    """TeacherNoteReadStatus用のカスタムManager"""

    def get_queryset(self):
        return TeacherNoteReadStatusQuerySet(self.model, using=self._db)

    def with_related(self):
        return self.get_queryset().with_related()


class TeacherNoteReadStatus(models.Model):
    """担任メモの既読状態管理（学年共有アラート用）"""

    # カスタムManager
    objects = TeacherNoteReadStatusManager()

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="note_read_statuses",
        verbose_name="担任",
    )
    note = models.ForeignKey(
        "TeacherNote",
        on_delete=models.CASCADE,
        related_name="read_statuses",
        verbose_name="担任メモ",
    )
    read_at = models.DateTimeField(
        "既読日時",
        auto_now_add=True,
    )

    class Meta:
        unique_together = [["teacher", "note"]]
        verbose_name = "担任メモ既読状態"
        verbose_name_plural = "担任メモ既読状態"
        ordering = ["-read_at"]
        indexes = [
            models.Index(fields=["teacher", "note"]),
        ]

    def __str__(self):
        teacher_name = self.teacher.get_full_name() or self.teacher.username
        note_info = f"Note #{self.note.id}"
        return f"{teacher_name} - {note_info} ({self.read_at.strftime('%Y-%m-%d %H:%M')})"


class AttendanceStatus(models.TextChoices):
    """出席状況"""

    PRESENT = "present", "出席"
    ABSENT = "absent", "欠席"
    LATE = "late", "遅刻"
    EARLY_LEAVE = "early_leave", "早退"


class AbsenceReason(models.TextChoices):
    """欠席理由"""

    ILLNESS = "illness", "病気"
    FAMILY = "family", "家庭の都合"
    OTHER = "other", "その他"


class DailyAttendanceQuerySet(models.QuerySet):
    """DailyAttendance用のQuerySet"""

    def with_related(self):
        """関連オブジェクトをprefetch（N+1クエリ解消）"""
        return self.select_related("student", "classroom", "noted_by")


class DailyAttendanceManager(models.Manager):
    """DailyAttendance用のカスタムManager"""

    def get_queryset(self):
        return DailyAttendanceQuerySet(self.model, using=self._db)

    def with_related(self):
        return self.get_queryset().with_related()


class DailyAttendance(models.Model):
    """出席記録（学級閉鎖判断の基礎データ）"""

    # カスタムManager
    objects = DailyAttendanceManager()

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name="生徒",
    )
    classroom = models.ForeignKey(
        "ClassRoom",
        on_delete=models.PROTECT,
        related_name="attendance_records",
        verbose_name="クラス",
    )
    date = models.DateField("日付")
    status = models.CharField(
        "出席状況",
        max_length=20,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.PRESENT,
    )
    absence_reason = models.CharField(
        "欠席理由",
        max_length=20,
        choices=AbsenceReason.choices,
        null=True,
        blank=True,
        help_text="欠席の場合のみ必須",
    )
    noted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_attendance",
        null=True,
        blank=True,
        verbose_name="記録者（担任）",
    )
    noted_at = models.DateTimeField("記録日時", auto_now_add=True)

    class Meta:
        verbose_name = "出席記録"
        verbose_name_plural = "出席記録"
        unique_together = ["student", "date"]
        ordering = ["-date", "student__last_name", "student__first_name"]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["absence_reason"]),
        ]

    def __str__(self):
        student_name = self.student.get_full_name() or self.student.username
        return f"{student_name} - {self.date} ({self.get_status_display()})"

    def clean(self):
        """バリデーション"""
        from django.core.exceptions import ValidationError

        # 欠席の場合は理由必須
        if self.status == AttendanceStatus.ABSENT and not self.absence_reason:
            raise ValidationError(
                {
                    "absence_reason": "欠席の場合は理由を選択してください",
                },
            )

        # 欠席以外の場合は理由不要
        if self.status != AttendanceStatus.ABSENT and self.absence_reason:
            raise ValidationError(
                {
                    "absence_reason": "欠席以外の場合は理由を選択しないでください",
                },
            )

    @classmethod
    def get_or_create_for_date(cls, classroom, date, teacher):
        """指定日の出席記録を取得または作成（全生徒分）"""
        students = classroom.students.all()
        records = []
        for student in students:
            record, _created = cls.objects.get_or_create(
                student=student,
                date=date,
                defaults={
                    "classroom": classroom,
                    "status": AttendanceStatus.PRESENT,
                    "noted_by": teacher,
                },
            )
            records.append(record)
        return records

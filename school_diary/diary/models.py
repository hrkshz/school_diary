from django.conf import settings
from django.core.validators import MaxValueValidator
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from kits.audit.models import AuditMixin


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


class DiaryEntry(models.Model):
    """連絡帳エントリー"""

    # 体調・メンタルの選択肢
    CONDITION_CHOICES = [
        (1, "とても悪い"),
        (2, "悪い"),
        (3, "普通"),
        (4, "良い"),
        (5, "とても良い"),
    ]

    MENTAL_CHOICES = [
        (1, "とても落ち込んでいる"),
        (2, "落ち込んでいる"),
        (3, "普通"),
        (4, "元気"),
        (5, "とても元気"),
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
        default=3,
    )
    mental_condition = models.IntegerField(
        "メンタル",
        choices=MENTAL_CHOICES,
        default=3,
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

    def save(self, *args, **kwargs):
        """保存時の自動処理"""
        # 新規作成時にclassroomを自動設定
        if not self.pk and not self.classroom:
            from .utils import get_current_classroom

            self.classroom = get_current_classroom(self.student)

        # 既存データの場合、internal_actionの変更を検知
        if self.pk:
            try:
                old = DiaryEntry.objects.get(pk=self.pk)
                # internal_actionが変更され、まだ対応済みでない場合はリセット
                if old.internal_action != self.internal_action and self.action_status == ActionStatus.COMPLETED:
                    self.action_status = ActionStatus.PENDING
                    self.action_completed_at = None
                    self.action_completed_by = None
            except DiaryEntry.DoesNotExist:
                pass

        # internal_actionの値に応じて自動設定
        if not self.internal_action or self.internal_action == "":
            # 対応記録がない場合は「対応不要」
            self.action_status = ActionStatus.NOT_REQUIRED

        super().save(*args, **kwargs)

    def mark_as_read(self, teacher):
        """既読処理(イイネスタンプ)"""
        self.is_read = True
        self.read_by = teacher
        self.read_at = timezone.now()
        self.save()

    def mark_action_completed(self, teacher, note=""):
        """対応完了処理"""
        self.action_status = ActionStatus.COMPLETED
        self.action_completed_at = timezone.now()
        self.action_completed_by = teacher
        if note:
            self.action_note = note
        self.save()

    @property
    def is_editable(self):
        """編集可能かどうか(既読前のみ編集可)"""
        return not self.is_read


class ClassRoom(models.Model):
    """クラス情報"""

    CLASS_NAME_CHOICES = [
        ("A", "A組"),
        ("B", "B組"),
        ("C", "C組"),
    ]

    GRADE_CHOICES = [
        (1, "1年"),
        (2, "2年"),
        (3, "3年"),
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
        verbose_name="担任",
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


class UserProfile(AuditMixin):
    """ユーザープロフィール（役割ベースの権限管理、変更履歴を自動記録）"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="ユーザー",
    )

    ROLE_CHOICES = [
        ("student", "生徒"),
        ("teacher", "担任"),
        ("grade_leader", "学年主任"),
        ("school_leader", "教頭/校長"),
    ]
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

    class Meta:
        verbose_name = "ユーザープロフィール"
        verbose_name_plural = "ユーザープロフィール"

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class TeacherNote(models.Model):
    """担任メモ（生徒の長期的な観察記録・引継ぎ情報）"""

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


class TeacherNoteReadStatus(models.Model):
    """担任メモの既読状態管理（学年共有アラート用）"""

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


class DailyAttendance(models.Model):
    """出席記録（学級閉鎖判断の基礎データ）"""

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

    @classmethod
    def get_or_create_for_date(cls, classroom, date, teacher):
        """指定日の出席記録を取得または作成（全生徒分）"""
        students = classroom.students.all()
        records = []
        for student in students:
            record, created = cls.objects.get_or_create(
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

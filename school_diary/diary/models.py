from django.conf import settings
from django.db import models
from django.utils import timezone


class DiaryEntry(models.Model):
    """連絡帳エントリー"""

    # 体調・メンタルの選択肢
    CONDITION_CHOICES = [
        (1, 'とても悪い'),
        (2, '悪い'),
        (3, '普通'),
        (4, '良い'),
        (5, 'とても良い'),
    ]

    MENTAL_CHOICES = [
        (1, 'とても落ち込んでいる'),
        (2, '落ち込んでいる'),
        (3, '普通'),
        (4, '元気'),
        (5, 'とても元気'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diary_entries',
        verbose_name='生徒',
    )
    entry_date = models.DateField(
        '記載日',
        help_text='前登校日の日付',
    )
    submission_date = models.DateTimeField(
        '提出日時',
        default=timezone.now,
    )

    health_condition = models.IntegerField(
        '体調',
        choices=CONDITION_CHOICES,
        default=3,
    )
    mental_condition = models.IntegerField(
        'メンタル',
        choices=MENTAL_CHOICES,
        default=3,
    )
    reflection = models.TextField(
        '今日の振り返り',
        help_text='今日あったこと、学んだこと、感じたことなど',
    )

    is_read = models.BooleanField(
        '既読',
        default=False,
    )
    read_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='read_diary_entries',
        null=True,
        blank=True,
        verbose_name='既読者（担任）',
    )
    read_at = models.DateTimeField(
        '既読日時',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = '連絡帳エントリー'
        verbose_name_plural = '連絡帳エントリー'
        unique_together = ['student', 'entry_date']
        ordering = ['-entry_date', 'student__last_name', 'student__first_name']
        indexes = [
            models.Index(fields=['entry_date']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        return f'{self.student.get_full_name() or self.student.username} - {self.entry_date}'

    def mark_as_read(self, teacher):
        """既読処理（イイネスタンプ）"""
        self.is_read = True
        self.read_by = teacher
        self.read_at = timezone.now()
        self.save()

    @property
    def is_editable(self):
        """編集可能かどうか（既読前のみ編集可）"""
        return not self.is_read


class ClassRoom(models.Model):
    """クラス情報"""

    CLASS_NAME_CHOICES = [
        ('A', 'A組'),
        ('B', 'B組'),
        ('C', 'C組'),
    ]

    GRADE_CHOICES = [
        (1, '1年'),
        (2, '2年'),
        (3, '3年'),
    ]

    grade = models.IntegerField(
        '学年',
        choices=GRADE_CHOICES,
    )
    class_name = models.CharField(
        'クラス名',
        max_length=10,
        choices=CLASS_NAME_CHOICES,
    )
    academic_year = models.IntegerField(
        '年度',
        default=2025,
    )
    homeroom_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='homeroom_classes',
        null=True,
        blank=True,
        verbose_name='担任',
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='classes',
        verbose_name='生徒',
        blank=True,
    )

    class Meta:
        verbose_name = 'クラス'
        verbose_name_plural = 'クラス'
        unique_together = ['grade', 'class_name', 'academic_year']
        ordering = ['academic_year', 'grade', 'class_name']

    def __str__(self):
        return f'{self.academic_year}年度 {self.get_grade_display()}{self.get_class_name_display()}'

    @property
    def student_count(self):
        """生徒数を返す"""
        return self.students.count()


class TeacherNote(models.Model):
    """担任メモ（課題2: 担任間共有機能用）"""

    diary_entry = models.ForeignKey(
        DiaryEntry,
        on_delete=models.CASCADE,
        related_name='teacher_notes',
        verbose_name='連絡帳エントリー',
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_notes',
        verbose_name='担任',
    )
    note = models.TextField(
        'メモ内容',
        help_text='気になったこと、学年会議で共有したいことなど',
    )
    is_shared = models.BooleanField(
        '学年会議で共有',
        default=False,
        help_text='学年会議で共有する場合はチェック',
    )
    created_at = models.DateTimeField(
        '作成日時',
        default=timezone.now,
    )

    class Meta:
        verbose_name = '担任メモ'
        verbose_name_plural = '担任メモ'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.teacher.get_full_name() or self.teacher.username} → {self.diary_entry.student.get_full_name()}'

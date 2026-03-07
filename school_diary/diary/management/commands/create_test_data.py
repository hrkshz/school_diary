"""統合テストデータ作成コマンド

管理画面から実行される統一テストデータ作成コマンド
"""

import random
from datetime import date, timedelta

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from school_diary.diary.academic_year import get_current_academic_year
from school_diary.diary.models import (
    AbsenceReason,
    ActionStatus,
    AttendanceStatus,
    ClassRoom,
    ConditionLevel,
    DailyAttendance,
    DiaryEntry,
    InternalAction,
    PublicReaction,
    TeacherNote,
    UserProfile,
)

User = get_user_model()


class Command(BaseCommand):
    help = "統合テストデータ作成コマンド（管理画面用）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clean",
            action="store_true",
            help="既存のテストデータを削除してから作成",
        )
        parser.add_argument(
            "--diary-days",
            type=int,
            default=30,
            help="日記データの作成日数（デフォルト: 30日）",
        )
        parser.add_argument(
            "--students-per-class",
            type=int,
            default=30,
            help="クラスあたりの生徒数（デフォルト: 30名）",
        )
        parser.add_argument(
            "--no-special-patterns",
            action="store_true",
            help="特別パターン（P0/P1/P1.5等）を作成しない",
        )

    def handle(self, *args, **options):
        self.clean = options["clean"]
        self.diary_days = options["diary_days"]
        self.students_per_class = options["students_per_class"]
        self.no_special_patterns = options["no_special_patterns"]

        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("統合テストデータ作成開始"))
        self.stdout.write(self.style.SUCCESS("=" * 50))

        try:
            with transaction.atomic():
                if self.clean:
                    self._clean_existing_data()

                # データ作成
                self._create_admin()
                self._create_principal()
                self._create_grade_leaders()
                classrooms = self._create_classrooms()
                self._create_teachers(classrooms)
                students = self._create_students(classrooms)
                self._create_diaries(students)

                if not self.no_special_patterns:
                    self._create_special_patterns(classrooms)

                self._create_some_read_diaries(classrooms)
                self._create_teacher_notes(classrooms)
                self._create_attendance_records(classrooms)

                self._show_statistics()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ エラーが発生しました: {e}"))
            raise

    def _clean_existing_data(self):
        """既存テストデータを削除"""
        self.stdout.write(self.style.WARNING("\n【既存データクリーンアップ】"))

        # 日記エントリ削除
        diary_count = DiaryEntry.objects.count()
        DiaryEntry.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"✓ 日記: {diary_count}件削除"))

        # 出席記録削除
        attendance_count = DailyAttendance.objects.count()
        DailyAttendance.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"✓ 出席記録: {attendance_count}件削除"))

        # 担任メモ削除
        note_count = TeacherNote.objects.count()
        TeacherNote.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"✓ 担任メモ: {note_count}件削除"))

        # クラス削除
        classroom_count = ClassRoom.objects.count()
        ClassRoom.objects.all().delete()
        self.stdout.write(self.style.WARNING(f"✓ クラス: {classroom_count}件削除"))

        # ユーザー削除（is_superuser以外）
        user_count = User.objects.filter(is_superuser=False).count()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write(self.style.WARNING(f"✓ ユーザー: {user_count}名削除"))

        self.stdout.write(self.style.SUCCESS("✓ クリーンアップ完了"))

    def _create_admin(self):
        """管理者作成"""
        self.stdout.write(self.style.SUCCESS("\n【管理者作成】"))
        email = "admin@example.com"

        if User.objects.filter(email=email, is_superuser=True).exists():
            self.stdout.write(self.style.WARNING(f"⚠️  {email}は既に存在します"))
            return

        if not User.objects.filter(email=email).exists():
            admin = User.objects.create_superuser(
                username=email,
                email=email,
                password="password123",
                first_name="管理者",
                last_name="システム",
            )
            EmailAddress.objects.get_or_create(
                user=admin,
                email=email,
                defaults={"verified": True, "primary": True},
            )
            self.stdout.write(self.style.SUCCESS(f"✅ {email}を作成"))

    def _create_principal(self):
        """校長作成"""
        self.stdout.write(self.style.SUCCESS("\n【校長作成】"))
        email = "principal@example.com"

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"⚠️  {email}は既に存在します"))
            return

        principal = User.objects.create_user(
            username=email,
            email=email,
            password="password123",
            first_name="太郎",
            last_name="校長",
        )
        EmailAddress.objects.get_or_create(
            user=principal,
            email=email,
            defaults={"verified": True, "primary": True},
        )
        principal.profile.role = UserProfile.ROLE_SCHOOL_LEADER
        principal.profile.save()
        self.stdout.write(self.style.SUCCESS(f"✅ {email}を作成"))

    def _create_grade_leaders(self):
        """学年主任3名作成"""
        self.stdout.write(self.style.SUCCESS("\n【学年主任作成】"))

        for grade in [1, 2, 3]:
            email = f"grade_leader_{grade}@example.com"
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f"⚠️  {email}は既に存在します"))
                continue

            user = User.objects.create_user(
                username=email,
                email=email,
                password="password123",
                first_name=f"{grade}年",
                last_name="主任",
            )
            EmailAddress.objects.get_or_create(
                user=user,
                email=email,
                defaults={"verified": True, "primary": True},
            )
            user.profile.role = UserProfile.ROLE_GRADE_LEADER
            user.profile.managed_grade = grade
            user.profile.save()
            self.stdout.write(self.style.SUCCESS(f"✅ {email}を作成（{grade}年主任）"))

    def _create_classrooms(self):
        """クラス9個作成"""
        self.stdout.write(self.style.SUCCESS("\n【クラス作成】"))
        classrooms = []

        for grade in [1, 2, 3]:
            for class_name in ["A", "B", "C"]:
                classroom, created = ClassRoom.objects.get_or_create(
                    grade=grade,
                    class_name=class_name,
                    academic_year=get_current_academic_year(),
                    defaults={"homeroom_teacher": None},
                )
                classrooms.append(classroom)
                if created:
                    self.stdout.write(self.style.SUCCESS(f"✅ {classroom}を作成"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️  {classroom}は既に存在します"))

        return classrooms

    def _create_teachers(self, classrooms):
        """担任9名作成"""
        self.stdout.write(self.style.SUCCESS("\n【担任作成】"))

        for idx, classroom in enumerate(classrooms):
            grade = classroom.grade
            class_name = classroom.class_name
            email = f"teacher_{grade}_{class_name.lower()}@example.com"

            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                self.stdout.write(self.style.WARNING(f"⚠️  {email}は既に存在します"))
            else:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password="password123",
                    first_name=f"{grade}年{class_name}組",
                    last_name="担任",
                )
                EmailAddress.objects.get_or_create(
                    user=user,
                    email=email,
                    defaults={"verified": True, "primary": True},
                )
                user.profile.role = UserProfile.ROLE_TEACHER
                user.profile.save()
                self.stdout.write(self.style.SUCCESS(f"✅ {email}を作成"))

            # クラスに担任を割り当て
            classroom.homeroom_teacher = user
            classroom.save()

    def _create_students(self, classrooms):
        """生徒作成"""
        self.stdout.write(self.style.SUCCESS(f"\n【生徒作成】各クラス{self.students_per_class}名"))

        last_names = [
            "佐藤", "鈴木", "高橋", "田中", "伊藤",
            "渡辺", "山本", "中村", "小林", "加藤",
            "吉田", "山田", "佐々木", "山口", "松本",
            "井上", "木村", "林", "斉藤", "清水",
            "山崎", "森", "池田", "橋本", "阿部",
            "石川", "山下", "中島", "石井", "小川",
        ]
        first_names = [
            "太郎", "花子", "一郎", "美咲", "健太",
            "さくら", "翔太", "愛美", "大輔", "結衣",
            "蓮", "陽菜", "颯太", "葵", "悠真",
            "結愛", "大和", "心春", "陽翔", "凛",
            "陽向", "芽依", "湊", "莉子", "朝陽",
            "美羽", "悠斗", "彩花", "優斗", "陽葵",
        ]

        all_students = []
        student_counter = 1

        for classroom in classrooms:
            self.stdout.write(f"\n{classroom}の生徒を作成中...")
            for i in range(self.students_per_class):
                email = f"student_{classroom.grade}_{classroom.class_name.lower()}_{i+1:02d}@example.com"

                last_name = last_names[(student_counter - 1) % len(last_names)]
                first_name = first_names[(student_counter - 1) % len(first_names)]

                if User.objects.filter(email=email).exists():
                    student = User.objects.get(email=email)
                else:
                    student = User.objects.create_user(
                        username=email,
                        email=email,
                        password="password123",
                        first_name=first_name,
                        last_name=last_name,
                    )
                    EmailAddress.objects.get_or_create(
                        user=student,
                        email=email,
                        defaults={"verified": True, "primary": True},
                    )
                    student.profile.role = UserProfile.ROLE_STUDENT
                    student.profile.save()

                if not classroom.students.filter(id=student.id).exists():
                    classroom.students.add(student)

                all_students.append((student, classroom))
                student_counter += 1

            self.stdout.write(self.style.SUCCESS(f"✅ {classroom}: {self.students_per_class}名作成完了"))

        return all_students

    def _create_diaries(self, students):
        """日記作成"""
        self.stdout.write(self.style.SUCCESS(f"\n【日記作成】過去{self.diary_days}日分"))

        today = date.today()
        reflections = [
            "今日は体育の授業で頑張りました。次は算数のテストを頑張ります。",
            "友達と一緒に給食を食べて楽しかったです。",
            "宿題が多くて大変でしたが、全部終わらせました。",
            "クラスマッチで優勝できて嬉しかったです。",
            "英語のテストで良い点が取れました。",
            "部活動で新しいことを学びました。",
            "今日は少し疲れましたが、充実した1日でした。",
            "先生に褒められて嬉しかったです。",
            "明日の遠足が楽しみです。",
            "友達と協力してプロジェクトを完成させました。",
        ]

        diary_count = 0
        for day_offset in range(self.diary_days):
            entry_date = today - timedelta(days=day_offset + 1)

            for student, classroom in students:
                # 提出率80%
                if random.random() > 0.8:
                    continue

                if DiaryEntry.objects.filter(student=student, entry_date=entry_date).exists():
                    continue

                DiaryEntry.objects.create(
                    student=student,
                    classroom=classroom,
                    entry_date=entry_date,
                    submission_date=timezone.now() - timedelta(days=day_offset),
                    health_condition=random.choice([
                        ConditionLevel.VERY_GOOD,
                        ConditionLevel.GOOD,
                        ConditionLevel.NORMAL,
                        ConditionLevel.NORMAL,
                        ConditionLevel.NORMAL,
                    ]),
                    mental_condition=random.choice([
                        ConditionLevel.VERY_GOOD,
                        ConditionLevel.GOOD,
                        ConditionLevel.NORMAL,
                        ConditionLevel.NORMAL,
                        ConditionLevel.NORMAL,
                    ]),
                    reflection=random.choice(reflections),
                )
                diary_count += 1

        self.stdout.write(self.style.SUCCESS(f"\n合計 {diary_count}件の日記を作成"))

    def _create_special_patterns(self, classrooms):
        """特別パターン作成"""
        self.stdout.write(self.style.SUCCESS("\n【特別パターン作成】"))

        classroom_1a = classrooms[0]
        today = date.today()
        yesterday = today - timedelta(days=1)

        students = list(classroom_1a.students.all()[:5])
        if len(students) < 5:
            self.stdout.write(self.style.WARNING("⚠️  生徒が5名未満のためスキップ"))
            return

        teacher = classroom_1a.homeroom_teacher

        # P0: メンタル★1
        student_p0 = students[0]
        DiaryEntry.objects.update_or_create(
            student=student_p0,
            entry_date=yesterday,
            defaults={
                "classroom": classroom_1a,
                "submission_date": timezone.now() - timedelta(hours=12),
                "health_condition": ConditionLevel.BAD,
                "mental_condition": ConditionLevel.VERY_BAD,
                "reflection": "最近とても気分が沈んでいて、学校に行くのがつらいです。",
            },
        )
        self.stdout.write(self.style.SUCCESS(f"✅ P0: {student_p0.get_full_name()}"))

        # P1: 3日連続メンタル低下
        student_p1 = students[1]
        for i, mental in enumerate([ConditionLevel.GOOD, ConditionLevel.NORMAL, ConditionLevel.BAD]):
            entry_date = today - timedelta(days=i + 1)
            DiaryEntry.objects.update_or_create(
                student=student_p1,
                entry_date=entry_date,
                defaults={
                    "classroom": classroom_1a,
                    "submission_date": timezone.now() - timedelta(days=i, hours=12),
                    "health_condition": ConditionLevel.NORMAL,
                    "mental_condition": mental,
                    "reflection": f"だんだん気分が落ち込んできました。",
                },
            )
        self.stdout.write(self.style.SUCCESS(f"✅ P1: {student_p1.get_full_name()}"))

        # P1.5: タスク化済み
        student_p15 = students[2]
        DiaryEntry.objects.update_or_create(
            student=student_p15,
            entry_date=yesterday,
            defaults={
                "classroom": classroom_1a,
                "submission_date": timezone.now() - timedelta(hours=18),
                "health_condition": ConditionLevel.NORMAL,
                "mental_condition": ConditionLevel.BAD,
                "reflection": "家族のことで悩んでいます。",
                "is_read": True,
                "read_by": teacher,
                "read_at": timezone.now() - timedelta(hours=6),
                "public_reaction": PublicReaction.SUPPORT,
                "internal_action": InternalAction.PARENT_CONTACTED,
                "action_status": ActionStatus.IN_PROGRESS,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"✅ P1.5: {student_p15.get_full_name()}"))

        # P3: 既読済み
        student_p3 = students[4]
        DiaryEntry.objects.update_or_create(
            student=student_p3,
            entry_date=yesterday,
            defaults={
                "classroom": classroom_1a,
                "submission_date": timezone.now() - timedelta(hours=20),
                "health_condition": ConditionLevel.VERY_GOOD,
                "mental_condition": ConditionLevel.VERY_GOOD,
                "reflection": "今日はとても楽しい1日でした。",
                "is_read": True,
                "read_by": teacher,
                "read_at": timezone.now() - timedelta(hours=4),
                "public_reaction": PublicReaction.EXCELLENT,
                "action_status": ActionStatus.NOT_REQUIRED,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"✅ P3: {student_p3.get_full_name()}"))

    def _create_some_read_diaries(self, classrooms):
        """既読データ作成"""
        self.stdout.write(self.style.SUCCESS("\n【既読データ作成】"))

        today = date.today()
        reactions = [
            PublicReaction.THUMBS_UP,
            PublicReaction.WELL_DONE,
            PublicReaction.GOOD_EFFORT,
            PublicReaction.CHECKED,
        ]

        read_count = 0
        for classroom in classrooms[:3]:
            if not classroom.homeroom_teacher:
                continue

            teacher = classroom.homeroom_teacher
            diaries = DiaryEntry.objects.filter(
                classroom=classroom,
                entry_date__gte=today - timedelta(days=3),
                is_read=False,
            )

            for diary in diaries:
                if random.random() > 0.5:
                    continue

                diary.is_read = True
                diary.read_by = teacher
                diary.read_at = timezone.now() - timedelta(hours=random.randint(1, 48))
                diary.public_reaction = random.choice(reactions)
                diary.action_status = ActionStatus.NOT_REQUIRED
                diary.save()
                read_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ {read_count}件の日記を既読に設定"))

    def _create_teacher_notes(self, classrooms):
        """担任メモ作成"""
        self.stdout.write(self.style.SUCCESS("\n【担任メモ作成】"))

        classroom_1a = classrooms[0]
        teacher_1a = classroom_1a.homeroom_teacher
        if not teacher_1a:
            return

        students = list(classroom_1a.students.all()[:2])
        if len(students) < 2:
            return

        TeacherNote.objects.get_or_create(
            student=students[0],
            teacher=teacher_1a,
            defaults={
                "note": "最近元気がない様子。継続的に様子を見る必要あり。",
                "is_shared": False,
            },
        )

        TeacherNote.objects.get_or_create(
            student=students[1],
            teacher=teacher_1a,
            defaults={
                "note": "家庭環境の変化があり、配慮が必要。",
                "is_shared": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("✅ 担任メモ作成完了"))

    def _create_attendance_records(self, classrooms):
        """出席記録作成"""
        self.stdout.write(self.style.SUCCESS("\n【出席記録作成】"))

        today = date.today()
        total_count = 0

        for classroom in classrooms[:3]:
            if not classroom.homeroom_teacher:
                continue

            teacher = classroom.homeroom_teacher
            students = list(classroom.students.all())

            for i, student in enumerate(students):
                if i < len(students) - 5:
                    DailyAttendance.objects.get_or_create(
                        student=student,
                        classroom=classroom,
                        date=today,
                        defaults={
                            "status": AttendanceStatus.PRESENT,
                            "noted_by": teacher,
                        },
                    )
                    total_count += 1
                elif i == len(students) - 5:
                    DailyAttendance.objects.get_or_create(
                        student=student,
                        classroom=classroom,
                        date=today,
                        defaults={
                            "status": AttendanceStatus.ABSENT,
                            "absence_reason": AbsenceReason.ILLNESS,
                            "noted_by": teacher,
                        },
                    )
                    total_count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ {total_count}件の出席記録を作成"))

    def _show_statistics(self):
        """統計表示"""
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(self.style.SUCCESS("✅ テストデータ作成完了"))
        self.stdout.write(self.style.SUCCESS("=" * 50))

        admin_count = User.objects.filter(is_superuser=True).count()
        school_leader_count = User.objects.filter(profile__role=UserProfile.ROLE_SCHOOL_LEADER).count()
        grade_leader_count = User.objects.filter(profile__role=UserProfile.ROLE_GRADE_LEADER).count()
        teacher_count = User.objects.filter(profile__role=UserProfile.ROLE_TEACHER).count()
        student_count = User.objects.filter(profile__role=UserProfile.ROLE_STUDENT).count()
        classroom_count = ClassRoom.objects.count()
        diary_count = DiaryEntry.objects.count()

        self.stdout.write(self.style.SUCCESS(f"管理者: {admin_count}名"))
        self.stdout.write(self.style.SUCCESS(f"校長: {school_leader_count}名"))
        self.stdout.write(self.style.SUCCESS(f"学年主任: {grade_leader_count}名"))
        self.stdout.write(self.style.SUCCESS(f"担任: {teacher_count}名"))
        self.stdout.write(self.style.SUCCESS(f"生徒: {student_count}名"))
        self.stdout.write(self.style.SUCCESS(f"クラス: {classroom_count}クラス"))
        self.stdout.write(self.style.SUCCESS(f"日記: {diary_count}件"))

        self.stdout.write(self.style.SUCCESS("\n全ユーザーのパスワード: password123"))
        self.stdout.write(self.style.SUCCESS("=" * 50))

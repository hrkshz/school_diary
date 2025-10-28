"""本番環境用テストデータ作成コマンド

学年主任3名、担任10名、生徒270名、日記過去7日分を作成
"""

import random
from datetime import date
from datetime import timedelta

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from school_diary.diary.models import AbsenceReason
from school_diary.diary.models import ActionStatus
from school_diary.diary.models import AttendanceStatus
from school_diary.diary.models import ClassRoom
from school_diary.diary.models import ConditionLevel
from school_diary.diary.models import DailyAttendance
from school_diary.diary.models import DiaryEntry
from school_diary.diary.models import InternalAction
from school_diary.diary.models import PublicReaction
from school_diary.diary.models import TeacherNote

User = get_user_model()


class Command(BaseCommand):
    help = "本番環境用テストデータ作成（学年主任3名、担任10名、生徒270名、日記7日分）"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("本番環境用テストデータ作成開始"))
        self.stdout.write(self.style.SUCCESS("=" * 50))

        # 1. 学年主任作成（3名）
        self.create_grade_leaders()

        # 2. クラス作成（9クラス）
        classrooms = self.create_classrooms()

        # 3. 担任作成（10名）
        self.create_teachers(classrooms)

        # 4. 生徒作成（270名）
        students = self.create_students(classrooms)

        # 5. 日記作成（過去7日分）
        self.create_diaries(students, classrooms)

        # 6. 特別パターン作成（P0/P1/P1.5/P2-1/P3）
        self.create_special_diary_patterns(classrooms)

        # 7. 既読・反応データ作成
        self.update_some_diaries_as_read(classrooms)

        # 8. 担任メモ作成
        self.create_teacher_notes(classrooms)

        # 9. 出席記録作成
        self.create_attendance_records(classrooms)

        # 統計表示
        self.show_statistics()

    def create_grade_leaders(self):
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
            user.profile.role = "grade_leader"
            user.profile.managed_grade = grade
            user.profile.save()
            self.stdout.write(self.style.SUCCESS(f"✅ {email}を作成（{grade}年主任）"))

    def create_classrooms(self):
        """クラス9個作成"""
        self.stdout.write(self.style.SUCCESS("\n【クラス作成】"))
        classrooms = []

        for grade in [1, 2, 3]:
            for class_name in ["A", "B", "C"]:
                classroom, created = ClassRoom.objects.get_or_create(
                    grade=grade,
                    class_name=class_name,
                    academic_year=2025,
                    defaults={"homeroom_teacher": None},
                )
                classrooms.append(classroom)
                if created:
                    self.stdout.write(self.style.SUCCESS(f"✅ {classroom}を作成"))
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️  {classroom}は既に存在します"))

        return classrooms

    def create_teachers(self, classrooms):
        """担任10名作成（9クラス分 + 1名予備）"""
        self.stdout.write(self.style.SUCCESS("\n【担任作成】"))

        # 9クラス分の担任
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
                user.profile.role = "teacher"
                user.profile.save()
                self.stdout.write(self.style.SUCCESS(f"✅ {email}を作成"))

            # クラスに担任を割り当て
            classroom.homeroom_teacher = user
            classroom.save()
            self.stdout.write(self.style.SUCCESS(f"   → {classroom}に割り当て"))

        # 10人目の予備担任
        email = "teacher_extra@example.com"
        if not User.objects.filter(email=email).exists():
            user = User.objects.create_user(
                username=email,
                email=email,
                password="password123",
                first_name="予備",
                last_name="担任",
            )
            EmailAddress.objects.get_or_create(
                user=user,
                email=email,
                defaults={"verified": True, "primary": True},
            )
            user.profile.role = "teacher"
            user.profile.save()
            self.stdout.write(self.style.SUCCESS(f"✅ {email}を作成（予備担任）"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️  {email}は既に存在します"))

    def create_students(self, classrooms):
        """生徒270名作成（各クラス30名）"""
        self.stdout.write(self.style.SUCCESS("\n【生徒作成】"))

        # 日本の一般的な姓と名
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
            "陽向", "芽依", "湊", "さくら", "朝陽",
            "莉子", "悠斗", "美羽", "優斗", "彩花",
        ]

        all_students = []
        student_counter = 1

        for classroom in classrooms:
            self.stdout.write(f"\n{classroom}の生徒を作成中...")
            for i in range(30):
                email = f"student_{classroom.grade}_{classroom.class_name.lower()}_{i+1:02d}@example.com"

                # 姓と名を決定
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
                    student.profile.role = "student"
                    student.profile.save()

                # クラスに追加
                if not classroom.students.filter(id=student.id).exists():
                    classroom.students.add(student)

                all_students.append((student, classroom))
                student_counter += 1

            self.stdout.write(self.style.SUCCESS(f"✅ {classroom}: 30名作成完了"))

        return all_students

    def create_diaries(self, students, classrooms):
        """日記作成（過去7日分、提出率80%）"""
        self.stdout.write(self.style.SUCCESS("\n【日記作成】過去7日分"))

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
        for day_offset in range(7):
            entry_date = today - timedelta(days=day_offset + 1)
            self.stdout.write(f"\n{entry_date}の日記作成中...")

            for student, classroom in students:
                # 提出率80%
                if random.random() > 0.8:
                    continue

                # 既存の日記をスキップ
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
                        ConditionLevel.NORMAL,  # 普通を多めに
                        ConditionLevel.NORMAL,
                    ]),
                    mental_condition=random.choice([
                        ConditionLevel.VERY_GOOD,
                        ConditionLevel.GOOD,
                        ConditionLevel.NORMAL,
                        ConditionLevel.NORMAL,  # 普通を多めに
                        ConditionLevel.NORMAL,
                    ]),
                    reflection=random.choice(reflections),
                )
                diary_count += 1

            self.stdout.write(self.style.SUCCESS(f"✅ {entry_date}: 作成完了"))

        self.stdout.write(self.style.SUCCESS(f"\n合計 {diary_count}件の日記を作成"))

    def create_special_diary_patterns(self, classrooms):
        """特別パターン作成（Inbox Pattern全カテゴリ検証用）"""
        self.stdout.write(self.style.SUCCESS("\n【特別パターン作成】Inbox Pattern検証用"))

        # 1年A組を使用
        classroom_1a = classrooms[0]  # 1年A組
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 生徒を取得（最初の5名を特別パターンに使用）
        students = list(classroom_1a.students.all()[:5])
        if len(students) < 5:
            self.stdout.write(self.style.WARNING("⚠️  生徒が5名未満のためスキップ"))
            return

        # P0: メンタル★1（最優先対応）
        student_p0 = students[0]
        DiaryEntry.objects.update_or_create(
            student=student_p0,
            entry_date=yesterday,
            defaults={
                "classroom": classroom_1a,
                "submission_date": timezone.now() - timedelta(hours=12),
                "health_condition": ConditionLevel.BAD,
                "mental_condition": ConditionLevel.VERY_BAD,  # ★1
                "reflection": "最近とても気分が沈んでいて、学校に行くのがつらいです。誰とも話したくない気分です。",
            },
        )
        self.stdout.write(self.style.SUCCESS(f"✅ P0重要: {student_p0.get_full_name()}（メンタル★1）"))

        # P1: 3日連続メンタル低下（早期警告）
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
                    "reflection": f"{i+1}日前の振り返りです。だんだん気分が落ち込んできました。",
                },
            )
        self.stdout.write(self.style.SUCCESS(f"✅ P1要注意: {student_p1.get_full_name()}（3日連続低下）"))

        # P1.5: 既読+タスク化済み（要対応タスク）
        student_p15 = students[2]
        teacher = classroom_1a.homeroom_teacher
        DiaryEntry.objects.update_or_create(
            student=student_p15,
            entry_date=yesterday,
            defaults={
                "classroom": classroom_1a,
                "submission_date": timezone.now() - timedelta(hours=18),
                "health_condition": ConditionLevel.NORMAL,
                "mental_condition": ConditionLevel.BAD,
                "reflection": "家族のことで悩んでいます。先生に相談したいです。",
                "is_read": True,
                "read_by": teacher,
                "read_at": timezone.now() - timedelta(hours=6),
                "public_reaction": PublicReaction.SUPPORT,
                "internal_action": InternalAction.PARENT_CONTACTED,
                "action_status": ActionStatus.IN_PROGRESS,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"✅ P1.5タスク: {student_p15.get_full_name()}（保護者連絡中）"))

        # P2-1: 今日未提出
        student_p21 = students[3]
        # 今日の日記を作成しない（未提出）
        self.stdout.write(self.style.SUCCESS(f"✅ P2-1未提出: {student_p21.get_full_name()}（今日未提出）"))

        # P3: 既読済み（完了）
        student_p3 = students[4]
        DiaryEntry.objects.update_or_create(
            student=student_p3,
            entry_date=yesterday,
            defaults={
                "classroom": classroom_1a,
                "submission_date": timezone.now() - timedelta(hours=20),
                "health_condition": ConditionLevel.VERY_GOOD,
                "mental_condition": ConditionLevel.VERY_GOOD,
                "reflection": "今日はとても楽しい1日でした。友達とたくさん遊びました！",
                "is_read": True,
                "read_by": teacher,
                "read_at": timezone.now() - timedelta(hours=4),
                "public_reaction": PublicReaction.EXCELLENT,
                "action_status": ActionStatus.NOT_REQUIRED,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"✅ P3完了: {student_p3.get_full_name()}（既読済み）"))

    def update_some_diaries_as_read(self, classrooms):
        """既読・反応データ作成（過去の日記の一部を既読にする）"""
        self.stdout.write(self.style.SUCCESS("\n【既読・反応データ作成】"))

        today = date.today()
        reactions = [
            PublicReaction.THUMBS_UP,
            PublicReaction.WELL_DONE,
            PublicReaction.GOOD_EFFORT,
            PublicReaction.CHECKED,
        ]

        read_count = 0
        for classroom in classrooms[:3]:  # 最初の3クラスのみ（1年A, B, C）
            if not classroom.homeroom_teacher:
                continue

            teacher = classroom.homeroom_teacher
            # 過去3日分の日記の50%を既読にする
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

    def create_teacher_notes(self, classrooms):
        """担任メモ作成（個人メモ・学年共有メモ）"""
        self.stdout.write(self.style.SUCCESS("\n【担任メモ作成】"))

        # 1年A組の最初の2名についてメモ作成
        classroom_1a = classrooms[0]
        teacher_1a = classroom_1a.homeroom_teacher
        if not teacher_1a:
            self.stdout.write(self.style.WARNING("⚠️  担任が設定されていないためスキップ"))
            return

        students = list(classroom_1a.students.all()[:2])
        if len(students) < 2:
            self.stdout.write(self.style.WARNING("⚠️  生徒が不足しているためスキップ"))
            return

        # 個人メモ
        TeacherNote.objects.get_or_create(
            student=students[0],
            teacher=teacher_1a,
            defaults={
                "note": "最近元気がない様子。継続的に様子を見る必要あり。",
                "is_shared": False,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"✅ 個人メモ作成: {students[0].get_full_name()}"))

        # 学年共有メモ
        TeacherNote.objects.get_or_create(
            student=students[1],
            teacher=teacher_1a,
            defaults={
                "note": "家庭環境の変化があり、配慮が必要。学年会議で情報共有済み。",
                "is_shared": True,
            },
        )
        self.stdout.write(self.style.SUCCESS(f"✅ 学年共有メモ作成: {students[1].get_full_name()}"))

        # 1年B組からも学年共有メモ作成（学年アラート表示用）
        classroom_1b = classrooms[1]
        teacher_1b = classroom_1b.homeroom_teacher
        if teacher_1b:
            student_1b = classroom_1b.students.first()
            if student_1b:
                TeacherNote.objects.get_or_create(
                    student=student_1b,
                    teacher=teacher_1b,
                    defaults={
                        "note": "クラスでのリーダーシップが見られる。学年行事での活躍が期待できる。",
                        "is_shared": True,
                    },
                )
                self.stdout.write(self.style.SUCCESS(f"✅ 学年共有メモ作成（1年B組）: {student_1b.get_full_name()}"))

    def create_attendance_records(self, classrooms):
        """出席記録作成（今日の出席状況）"""
        self.stdout.write(self.style.SUCCESS("\n【出席記録作成】"))

        today = date.today()
        total_count = 0

        for classroom in classrooms[:3]:  # 最初の3クラス（1年A, B, C）
            if not classroom.homeroom_teacher:
                continue

            teacher = classroom.homeroom_teacher
            students = list(classroom.students.all())

            # 大半を出席にする
            for i, student in enumerate(students):
                if i < len(students) - 5:
                    # 出席
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
                    # 欠席（病気）
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
                elif i == len(students) - 4:
                    # 欠席（家庭の都合）
                    DailyAttendance.objects.get_or_create(
                        student=student,
                        classroom=classroom,
                        date=today,
                        defaults={
                            "status": AttendanceStatus.ABSENT,
                            "absence_reason": AbsenceReason.FAMILY,
                            "noted_by": teacher,
                        },
                    )
                    total_count += 1
                elif i == len(students) - 3:
                    # 遅刻
                    DailyAttendance.objects.get_or_create(
                        student=student,
                        classroom=classroom,
                        date=today,
                        defaults={
                            "status": AttendanceStatus.LATE,
                            "noted_by": teacher,
                        },
                    )
                    total_count += 1
                elif i == len(students) - 2:
                    # 早退
                    DailyAttendance.objects.get_or_create(
                        student=student,
                        classroom=classroom,
                        date=today,
                        defaults={
                            "status": AttendanceStatus.EARLY_LEAVE,
                            "noted_by": teacher,
                        },
                    )
                    total_count += 1

            self.stdout.write(self.style.SUCCESS(f"✅ {classroom}: 出席記録作成完了"))

        self.stdout.write(self.style.SUCCESS(f"✅ 合計 {total_count}件の出席記録を作成"))

    def show_statistics(self):
        """統計表示"""
        self.stdout.write(self.style.SUCCESS("\n" + "=" * 50))
        self.stdout.write(self.style.SUCCESS("✅ テストデータ作成完了"))
        self.stdout.write(self.style.SUCCESS("=" * 50))

        admin_count = User.objects.filter(is_superuser=True).count()
        school_leader_count = User.objects.filter(profile__role="school_leader").count()
        grade_leader_count = User.objects.filter(profile__role="grade_leader").count()
        teacher_count = User.objects.filter(profile__role="teacher").count()
        student_count = User.objects.filter(profile__role="student").count()
        classroom_count = ClassRoom.objects.count()
        diary_count = DiaryEntry.objects.count()

        self.stdout.write(self.style.SUCCESS(f"管理者: {admin_count}名"))
        self.stdout.write(self.style.SUCCESS(f"校長・教頭: {school_leader_count}名"))
        self.stdout.write(self.style.SUCCESS(f"学年主任: {grade_leader_count}名"))
        self.stdout.write(self.style.SUCCESS(f"担任: {teacher_count}名"))
        self.stdout.write(self.style.SUCCESS(f"生徒: {student_count}名"))
        self.stdout.write(self.style.SUCCESS(f"クラス: {classroom_count}クラス"))
        self.stdout.write(self.style.SUCCESS(f"日記: {diary_count}件"))

        self.stdout.write(self.style.SUCCESS("\n全ユーザーのパスワード: password123"))
        self.stdout.write(self.style.SUCCESS("=" * 50))

"""Production Test Data Loading Command (USER_TESTING_MANUAL.md準拠)

本番環境・評価環境テストデータを作成するManagement Command

実行方法:
    python manage.py load_production_test_data --clear

機能:
    - USER_TESTING_MANUAL.mdに完全準拠
    - メールアドレスログイン（@example.com）
    - パスワード統一（password123）
    - 中学校（1-3年、各学年3クラス、各クラス30名）
    - Inbox Pattern全パターン（P0~P3）
    - 14日分の連絡帳データ

必須アカウント:
    - admin@example.com（システム管理者）
    - principal@example.com（校長/教頭）
    - grade_leader@example.com（1年生主任）
    - teacher_1_a@example.com（1年A組担任）
    - student_1_a_01@example.com（1年A組1番）
"""

import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from school_diary.diary.constants import GradeLevel
from school_diary.diary.models import ActionStatus
from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DiaryEntry
from school_diary.diary.models import InternalAction
from school_diary.diary.models import PublicReaction
from school_diary.diary.models import TeacherNote
from school_diary.diary.models import TeacherNoteReadStatus
from school_diary.diary.models import UserProfile

User = get_user_model()


class Command(BaseCommand):
    help = "本番環境・評価環境テストデータを作成（USER_TESTING_MANUAL.md準拠）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="既存のテストデータを削除してから作成",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("=" * 80))
        self.stdout.write(
            self.style.WARNING("本番環境テストデータ作成を開始します（USER_TESTING_MANUAL.md準拠）"),
        )
        self.stdout.write(self.style.WARNING("=" * 80))

        if options["clear"]:
            self.clear_data()

        try:
            with transaction.atomic():
                self.create_test_data()
                self.stdout.write(
                    self.style.SUCCESS("\n✅ テストデータ作成が完了しました！"),
                )
                self.print_summary()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n❌ エラーが発生しました: {e}"),
            )
            raise

    def clear_data(self):
        """既存のテストデータを削除"""
        self.stdout.write(self.style.WARNING("\n🗑️  既存データを削除中..."))

        # 逆順で削除（外部キー制約考慮）
        TeacherNoteReadStatus.objects.all().delete()
        TeacherNote.objects.all().delete()
        DiaryEntry.objects.all().delete()
        ClassRoom.objects.all().delete()
        UserProfile.objects.all().delete()

        # Userは1件ずつ削除（エラー時もスキップして続行）
        test_users = User.objects.filter(email__endswith="@example.com")
        deleted_count = 0
        error_count = 0
        for user in test_users:
            try:
                user.delete()
                deleted_count += 1
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.WARNING(f"⚠️  User削除エラー（{user.email}）: {e}"),
                )

        self.stdout.write(
            self.style.SUCCESS(f"✅ 既存データを削除しました（User: {deleted_count}件、エラー: {error_count}件）"),
        )

    def create_test_data(self):
        """テストデータ作成メイン処理"""
        self.stdout.write(self.style.WARNING("\n📝 テストデータ作成中..."))

        # 1. 必須アカウント作成（USER_TESTING_MANUAL.md準拠）
        self.create_required_accounts()

        # 2. 追加アカウント作成（全学年・全クラス・全生徒）
        self.create_additional_accounts()

        # 3. ClassRoom作成
        self.create_classrooms()

        # 4. DiaryEntry作成（14日分、Inbox Pattern全パターン）
        self.create_diary_entries()

        # 5. TeacherNote作成（共有メモ）
        self.create_teacher_notes()

    def create_required_accounts(self):
        """必須アカウント5つを作成（USER_TESTING_MANUAL.md準拠）"""
        self.stdout.write(self.style.WARNING("\n👥 必須アカウント作成中..."))

        # 1. システム管理者
        admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="password123",
            first_name="システム",
            last_name="管理者",
        )
        admin_user.profile.role = UserProfile.ROLE_ADMIN
        admin_user.profile.save()
        self.stdout.write("  ✅ admin@example.com / password123（システム管理者）")

        # 2. 校長/教頭
        principal_user = User.objects.create_user(
            username="principal",
            email="principal@example.com",
            password="password123",
            first_name="校長",
            last_name="先生",
        )
        principal_user.profile.role = UserProfile.ROLE_SCHOOL_LEADER
        principal_user.profile.save()
        self.stdout.write("  ✅ principal@example.com / password123（校長/教頭）")

        # 3. 1年生主任（grade_leader@example.com）
        grade_leader_user = User.objects.create_user(
            username="grade_leader",
            email="grade_leader@example.com",
            password="password123",
            first_name="1年",
            last_name="主任",
        )
        grade_leader_user.profile.role = UserProfile.ROLE_GRADE_LEADER
        grade_leader_user.profile.managed_grade = GradeLevel.GRADE_1
        grade_leader_user.profile.save()
        self.grade_leaders = {GradeLevel.GRADE_1: grade_leader_user}
        self.stdout.write("  ✅ grade_leader@example.com / password123（1年生主任）")

        # 4. 1年A組担任
        teacher_1_a_user = User.objects.create_user(
            username="teacher_1_a",
            email="teacher_1_a@example.com",
            password="password123",
            first_name="1年A組",
            last_name="担任",
        )
        teacher_1_a_user.profile.role = UserProfile.ROLE_TEACHER
        teacher_1_a_user.profile.save()
        self.teachers = {"1_a": teacher_1_a_user}
        self.stdout.write("  ✅ teacher_1_a@example.com / password123（1年A組担任）")

        # 5. 1年A組1番生徒
        student_1_a_01_user = User.objects.create_user(
            username="student_1_a_01",
            email="student_1_a_01@example.com",
            password="password123",
            first_name="太郎",
            last_name="田中",
        )
        # signalsで自動作成されたUserProfileはデフォルトでROLE_STUDENT
        self.students = {"1_a_01": student_1_a_01_user}
        self.stdout.write("  ✅ student_1_a_01@example.com / password123（1年A組1番）")

    def create_additional_accounts(self):
        """追加アカウント作成（全学年・全クラス・全生徒）"""
        self.stdout.write(self.style.WARNING("\n👥 追加アカウント作成中..."))

        japanese_surnames = [
            "田中", "鈴木", "佐藤", "高橋", "渡辺",
            "伊藤", "山本", "中村", "小林", "加藤",
            "吉田", "山田", "佐々木", "山口", "松本",
            "井上", "木村", "林", "斉藤", "清水",
            "山崎", "森", "池田", "橋本", "阿部",
            "石川", "前田", "藤田", "後藤", "長谷川",
        ]
        japanese_given_names = [
            "太郎", "次郎", "三郎", "花子", "美咲",
            "翔太", "拓也", "陽菜", "結衣", "さくら",
            "健太", "大輔", "ゆい", "あかり", "はるか",
            "颯太", "蓮", "葵", "凛", "咲",
            "悠斗", "陽斗", "心春", "陽葵", "結月",
            "蒼", "湊", "莉子", "美羽", "楓",
        ]

        # 2年・3年の学年主任
        for grade in [GradeLevel.GRADE_2, GradeLevel.GRADE_3]:
            username = f"grade_{grade}_leader"
            email = f"{username}@example.com"
            user = User.objects.create_user(
                username=username,
                email=email,
                password="password123",
                first_name=f"{grade}年",
                last_name="主任",
            )
            user.profile.role = UserProfile.ROLE_GRADE_LEADER
            user.profile.managed_grade = grade
            user.profile.save()
            self.grade_leaders[grade] = user

        # 全担任（9名）- teacher_1_aは既に作成済み
        for grade in [GradeLevel.GRADE_1, GradeLevel.GRADE_2, GradeLevel.GRADE_3]:
            for class_name in ["a", "b", "c"]:
                key = f"{grade}_{class_name}"
                if key == "1_a":  # 既に作成済み
                    continue
                username = f"teacher_{grade}_{class_name}"
                email = f"{username}@example.com"
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password="password123",
                    first_name=f"{grade}年{class_name.upper()}組",
                    last_name="担任",
                )
                user.profile.role = UserProfile.ROLE_TEACHER
                user.profile.save()
                self.teachers[key] = user

        # 全生徒（270名）- student_1_a_01は既に作成済み
        for grade in [GradeLevel.GRADE_1, GradeLevel.GRADE_2, GradeLevel.GRADE_3]:
            for class_name in ["a", "b", "c"]:
                for num in range(1, 31):  # 1-30
                    key = f"{grade}_{class_name}_{num:02d}"
                    if key == "1_a_01":  # 既に作成済み
                        continue
                    username = f"student_{grade}_{class_name}_{num:02d}"
                    email = f"{username}@example.com"
                    surname = random.choice(japanese_surnames)
                    given_name = random.choice(japanese_given_names)
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password="password123",
                        last_name=surname,
                        first_name=given_name,
                    )
                    # signalsで自動作成されたUserProfileはデフォルトでROLE_STUDENT
                    self.students[key] = user

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ ユーザー作成完了（合計: {User.objects.filter(email__endswith='@example.com').count()}名）",
            ),
        )

    def create_classrooms(self):
        """ClassRoom作成（学年・クラス・担任・生徒割り当て）"""
        self.stdout.write(self.style.WARNING("\n🏫 クラス作成中..."))

        self.classrooms = {}
        for grade in [GradeLevel.GRADE_1, GradeLevel.GRADE_2, GradeLevel.GRADE_3]:
            for class_name in ["a", "b", "c"]:
                classroom = ClassRoom.objects.create(
                    grade=grade,
                    class_name=class_name.upper(),
                    academic_year=2025,
                    homeroom_teacher=self.teachers[f"{grade}_{class_name}"],
                )

                # 学年主任を副担任に追加
                classroom.assistant_teachers.add(self.grade_leaders[grade])

                # 生徒を割り当て
                for num in range(1, 31):
                    key = f"{grade}_{class_name}_{num:02d}"
                    classroom.students.add(self.students[key])

                self.classrooms[f"{grade}_{class_name}"] = classroom

        self.stdout.write(
            self.style.SUCCESS(f"✅ クラス作成完了（合計: {ClassRoom.objects.count()}クラス）"),
        )

    def create_diary_entries(self):
        """DiaryEntry作成（14日分、Inbox Pattern全パターン）"""
        self.stdout.write(self.style.WARNING("\n📖 連絡帳データ作成中..."))

        today = timezone.now().date()

        # 1年A組のみ詳細データ作成（Inbox Pattern全パターン）
        classroom_1_a = self.classrooms["1_a"]
        students_1_a = list(classroom_1_a.students.all().order_by("username"))

        # Inbox Patternパターン割り当て
        p0_students = students_1_a[0:2]      # P0: メンタル★1（2名）
        p1_students = students_1_a[2:4]      # P1: 3日連続低下（2名）
        p1_5_students = students_1_a[4:7]    # P1.5: タスク設定済み（3名）
        p2_1_students = students_1_a[7:12]   # P2-1: 未提出（5名）
        p2_2_students = students_1_a[12:17]  # P2-2: 未読（5名）
        p2_3_students = students_1_a[17:22]  # P2-3: 反応待ち（5名）
        p3_students = students_1_a[22:30]    # P3: 完了（8名）

        # 14日分のデータ作成
        for days_ago in range(14, 0, -1):
            entry_date = today - timedelta(days=days_ago)

            # P0生徒（メンタル★1、最終日のみ）
            for student in p0_students:
                if days_ago == 1:
                    self._create_entry(
                        student, classroom_1_a, entry_date,
                        mental=1, health=3, is_read=False,
                    )
                else:
                    self._create_normal_entry(student, classroom_1_a, entry_date)

            # P1生徒（3日連続低下: 5→4→3）
            for student in p1_students:
                if days_ago == 3:
                    mental = 5
                elif days_ago == 2:
                    mental = 4
                elif days_ago == 1:
                    mental = 3
                else:
                    mental = random.randint(4, 5)
                self._create_entry(
                    student, classroom_1_a, entry_date,
                    mental=mental, health=4, is_read=(days_ago > 1),
                )

            # P1.5生徒（タスク設定済み）
            for student in p1_5_students:
                if days_ago == 1:
                    self._create_entry(
                        student, classroom_1_a, entry_date,
                        mental=3, health=3, is_read=True,
                        internal_action=InternalAction.NEEDS_FOLLOW_UP,
                        action_status=ActionStatus.PENDING,
                    )
                else:
                    self._create_normal_entry(student, classroom_1_a, entry_date)

            # P2-1生徒（未提出）: 昨日以降のエントリーなし
            for student in p2_1_students:
                if days_ago > 1:
                    self._create_normal_entry(student, classroom_1_a, entry_date)

            # P2-2生徒（未読）
            for student in p2_2_students:
                if days_ago == 1:
                    self._create_entry(
                        student, classroom_1_a, entry_date,
                        mental=4, health=4, is_read=False,
                    )
                else:
                    self._create_normal_entry(student, classroom_1_a, entry_date)

            # P2-3生徒（反応待ち）
            for student in p2_3_students:
                if days_ago == 1:
                    self._create_entry(
                        student, classroom_1_a, entry_date,
                        mental=4, health=4, is_read=True,
                        public_reaction=None,  # 既読だが反応なし
                    )
                else:
                    self._create_normal_entry(student, classroom_1_a, entry_date)

            # P3生徒（完了）
            for student in p3_students:
                if days_ago == 1:
                    self._create_entry(
                        student, classroom_1_a, entry_date,
                        mental=random.randint(4, 5),
                        health=random.randint(4, 5),
                        is_read=True,
                        public_reaction=PublicReaction.THUMBS_UP,
                    )
                else:
                    self._create_normal_entry(student, classroom_1_a, entry_date)

        # 他のクラスは通常データのみ（簡易版）
        for classroom_key, classroom in self.classrooms.items():
            if classroom_key == "1_a":
                continue
            students = list(classroom.students.all())
            for days_ago in range(14, 0, -1):
                entry_date = today - timedelta(days=days_ago)
                for student in students:
                    self._create_normal_entry(student, classroom, entry_date)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ 連絡帳データ作成完了（合計: {DiaryEntry.objects.count()}件）",
            ),
        )

    def _create_entry(
        self,
        student,
        classroom,
        entry_date,
        mental,
        health,
        is_read=False,
        public_reaction=None,
        internal_action=None,
        action_status=ActionStatus.PENDING,
    ):
        """DiaryEntry作成ヘルパー"""
        entry = DiaryEntry.objects.create(
            student=student,
            classroom=classroom,
            entry_date=entry_date,
            mental_condition=mental,
            health_condition=health,
            reflection=f"{entry_date}の振り返り。部活や勉強について。",
            is_read=is_read,
            public_reaction=public_reaction,
            internal_action=internal_action,
            action_status=action_status,
        )
        if is_read:
            entry.read_by = classroom.homeroom_teacher
            entry.read_at = timezone.now()
            entry.save()
        return entry

    def _create_normal_entry(self, student, classroom, entry_date):
        """通常のDiaryEntry作成（提出済み、既読、反応済み）"""
        return self._create_entry(
            student, classroom, entry_date,
            mental=random.randint(3, 5),
            health=random.randint(3, 5),
            is_read=True,
            public_reaction=PublicReaction.THUMBS_UP,
        )

    def create_teacher_notes(self):
        """TeacherNote作成（共有メモ・既読管理）"""
        self.stdout.write(self.style.WARNING("\n📝 共有メモ作成中..."))

        # 1年A組の担任が共有メモを作成
        classroom_1_a = self.classrooms["1_a"]
        teacher_1_a = classroom_1_a.homeroom_teacher
        students_1_a = list(classroom_1_a.students.all().order_by("username"))

        # 共有メモ作成（2件）
        note1 = TeacherNote.objects.create(
            teacher=teacher_1_a,
            student=students_1_a[0],
            note="最近、部活で悩んでいるようです。学年で共有します。",
            is_shared=True,
        )
        note2 = TeacherNote.objects.create(
            teacher=teacher_1_a,
            student=students_1_a[1],
            note="保護者面談希望あり。学年主任に報告済み。",
            is_shared=True,
        )

        # 既読管理（学年主任は既読）
        grade_leader = self.grade_leaders[GradeLevel.GRADE_1]
        TeacherNoteReadStatus.objects.create(teacher=grade_leader, note=note1)
        TeacherNoteReadStatus.objects.create(teacher=grade_leader, note=note2)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ 共有メモ作成完了（合計: {TeacherNote.objects.count()}件）",
            ),
        )

    def print_summary(self):
        """作成したデータのサマリー表示"""
        self.stdout.write(self.style.WARNING("\n" + "=" * 80))
        self.stdout.write(self.style.WARNING("📊 作成データサマリー"))
        self.stdout.write(self.style.WARNING("=" * 80))

        user_count = User.objects.filter(email__endswith="@example.com").count()
        self.stdout.write(f"ユーザー: {user_count}名")
        self.stdout.write("  - 必須アカウント: 5名")
        self.stdout.write("  - 学年主任: 3名")
        self.stdout.write("  - 担任: 9名")
        self.stdout.write("  - 生徒: 270名")
        self.stdout.write(f"クラス: {ClassRoom.objects.count()}クラス")
        self.stdout.write(f"連絡帳: {DiaryEntry.objects.count()}件")
        self.stdout.write(f"共有メモ: {TeacherNote.objects.count()}件")

        self.stdout.write(self.style.WARNING("\n" + "=" * 80))
        self.stdout.write(self.style.WARNING("🔐 必須ログイン情報（USER_TESTING_MANUAL.md準拠）"))
        self.stdout.write(self.style.WARNING("=" * 80))
        self.stdout.write("システム管理者: admin@example.com / password123")
        self.stdout.write("校長/教頭:     principal@example.com / password123")
        self.stdout.write("1年生主任:     grade_leader@example.com / password123")
        self.stdout.write("1年A組担任:   teacher_1_a@example.com / password123")
        self.stdout.write("1年A組1番:    student_1_a_01@example.com / password123")

        self.stdout.write(self.style.WARNING("\n" + "=" * 80))
        self.stdout.write(self.style.SUCCESS("✅ USER_TESTING_MANUAL.mdの全テストケースが実行可能です！"))
        self.stdout.write(self.style.WARNING("=" * 80))

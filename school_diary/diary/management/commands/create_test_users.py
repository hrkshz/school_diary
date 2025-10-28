from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from school_diary.diary.models import ClassRoom

User = get_user_model()


class Command(BaseCommand):
    help = "テストユーザーとクラスを作成"

    def handle(self, *args, **options):
        # 管理者作成（メールアドレスは小文字のみ）
        admin_email = "admin@example.com"
        if not User.objects.filter(username="admin").exists():
            admin = User.objects.create_superuser(
                username="admin",
                email=admin_email,
                password="password123",
            )
            # EmailAddress レコードを作成
            EmailAddress.objects.get_or_create(
                user=admin,
                email=admin_email,
                defaults={"verified": True, "primary": True},
            )
            self.stdout.write(self.style.SUCCESS("✅ 管理者を作成しました"))
        else:
            self.stdout.write(self.style.WARNING("⚠️  管理者は既に存在します"))

        # 校長作成（メールアドレスは小文字のみ）
        principal_email = "principal@example.com"
        if not User.objects.filter(username="principal").exists():
            principal = User.objects.create_user(
                username="principal",
                email=principal_email,
                password="password123",
                first_name="校長",
                last_name="田中",
            )
            # EmailAddress レコードを作成
            EmailAddress.objects.get_or_create(
                user=principal,
                email=principal_email,
                defaults={"verified": True, "primary": True},
            )
            # UserProfile の role 設定
            principal.profile.role = "school_leader"
            principal.profile.save()
            self.stdout.write(self.style.SUCCESS("✅ 校長を作成しました"))
        else:
            self.stdout.write(self.style.WARNING("⚠️  校長は既に存在します"))

        # 担任作成（各学年2名 = 6名、メールアドレスは小文字のみ）
        teachers = []
        for grade in [1, 2, 3]:
            for i in range(2):
                class_name = chr(97 + i)  # a, b (小文字)
                email = f"teacher_{grade}_{class_name}@example.com"
                if not User.objects.filter(username=email).exists():
                    teacher = User.objects.create_user(
                        username=email,
                        email=email,
                        password="password123",
                    )
                    # EmailAddress レコードを作成
                    EmailAddress.objects.get_or_create(
                        user=teacher,
                        email=email,
                        defaults={"verified": True, "primary": True},
                    )
                    teachers.append(teacher)
                    self.stdout.write(self.style.SUCCESS(f"✅ {email}を作成"))
                else:
                    teacher = User.objects.get(username=email)
                    teachers.append(teacher)
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  {email}は既に存在します"),
                    )

                # UserProfile の role 設定（新規・既存共通）
                # 1年A組担任は学年主任・校長を兼任（E2Eテスト用）
                if grade == 1 and i == 0:
                    teacher.profile.role = "school_leader"  # 校長権限
                    teacher.profile.managed_grade = grade
                    teacher.profile.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"   → {email}を校長兼学年主任（{grade}年）に設定"),
                    )
                else:
                    teacher.profile.role = "teacher"
                    teacher.profile.save()

        # クラス作成（各学年2クラス = 6クラス）
        classrooms = []
        for grade in [1, 2, 3]:
            for class_name in ["A", "B"]:
                teacher_index = (grade - 1) * 2 + (0 if class_name == "A" else 1)
                classroom, created = ClassRoom.objects.get_or_create(
                    grade=grade,
                    class_name=class_name,
                    academic_year=2025,
                    defaults={
                        "homeroom_teacher": teachers[teacher_index],
                    },
                )
                classrooms.append(classroom)
                if created:
                    self.stdout.write(self.style.SUCCESS(f"✅ {classroom}を作成"))
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  {classroom}は既に存在します"),
                    )

        # 生徒作成（各クラス5名 = 30名、メールアドレスは小文字のみ）
        # 日本の一般的な姓と名のリスト
        last_names = ["山田", "佐藤", "鈴木", "高橋", "田中", "伊藤", "渡辺", "中村", "小林", "加藤"]
        first_names = ["太郎", "花子", "一郎", "美咲", "健太", "さくら", "翔太", "愛美", "大輔", "結衣", "蓮", "陽菜", "颯太", "葵", "悠真"]

        for idx, classroom in enumerate(classrooms):
            for i in range(5):
                student_num = idx * 5 + i + 1
                email = f"student_{student_num:03d}@example.com"

                # 姓と名を決定（student_numに基づいて一意の組み合わせ）
                last_name = last_names[(student_num - 1) % len(last_names)]
                first_name = first_names[(student_num - 1) % len(first_names)]

                if not User.objects.filter(username=email).exists():
                    student = User.objects.create_user(
                        username=email,
                        email=email,
                        password="password123",
                        first_name=first_name,
                        last_name=last_name,
                    )
                    # EmailAddress レコードを作成
                    EmailAddress.objects.get_or_create(
                        user=student,
                        email=email,
                        defaults={"verified": True, "primary": True},
                    )
                    classroom.students.add(student)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ {email}を作成し{classroom}に追加",
                        ),
                    )
                else:
                    student = User.objects.get(username=email)
                    # 既存ユーザーにも姓名を設定（未設定の場合）
                    if not student.first_name or not student.last_name:
                        student.first_name = first_name
                        student.last_name = last_name
                        student.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✅ {email}に姓名を設定: {last_name} {first_name}",
                            ),
                        )
                    if not classroom.students.filter(id=student.id).exists():
                        classroom.students.add(student)
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️  {email}は既に存在しますが、{classroom}に追加しました",
                            ),
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️  {email}は既に{classroom}に存在します",
                            ),
                        )

        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("✅ テストデータ作成完了"))
        self.stdout.write(
            self.style.SUCCESS(
                f"管理者: {User.objects.filter(is_superuser=True).count()}名",
            ),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"担任: {User.objects.filter(username__contains='teacher_').count()}名",
            ),
        )
        self.stdout.write(
            self.style.SUCCESS(f"クラス: {ClassRoom.objects.count()}クラス"),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"生徒: {User.objects.filter(username__contains='student_').count()}名",
            ),
        )

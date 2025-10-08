from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from school_diary.diary.models import ClassRoom

User = get_user_model()


class Command(BaseCommand):
    help = "テストユーザーとクラスを作成"

    def handle(self, *args, **options):
        # 管理者作成
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin123")
            self.stdout.write(self.style.SUCCESS("✅ 管理者を作成しました"))
        else:
            self.stdout.write(self.style.WARNING("⚠️  管理者は既に存在します"))

        # 担任作成（各学年2名 = 6名）
        teachers = []
        for grade in [1, 2, 3]:
            for i in range(2):
                username = f"teacher_{grade}_{chr(65 + i)}"  # teacher_1_A, teacher_1_B
                if not User.objects.filter(username=username).exists():
                    teacher = User.objects.create_user(
                        username,
                        f"{username}@example.com",
                        "password123",
                    )
                    teachers.append(teacher)
                    self.stdout.write(self.style.SUCCESS(f"✅ {username}を作成"))
                else:
                    teacher = User.objects.get(username=username)
                    teachers.append(teacher)
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  {username}は既に存在します"),
                    )

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

        # 生徒作成（各クラス5名 = 30名）
        for idx, classroom in enumerate(classrooms):
            for i in range(5):
                student_num = idx * 5 + i + 1
                username = f"student_{student_num:03d}"  # student_001, student_002, ...
                if not User.objects.filter(username=username).exists():
                    student = User.objects.create_user(
                        username,
                        f"{username}@example.com",
                        "password123",
                    )
                    classroom.students.add(student)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ {username}を作成し{classroom}に追加",
                        ),
                    )
                else:
                    student = User.objects.get(username=username)
                    if not classroom.students.filter(id=student.id).exists():
                        classroom.students.add(student)
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️  {username}は既に存在しますが、{classroom}に追加しました",
                            ),
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️  {username}は既に{classroom}に存在します",
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
                f"担任: {User.objects.filter(username__startswith='teacher_').count()}名",
            ),
        )
        self.stdout.write(
            self.style.SUCCESS(f"クラス: {ClassRoom.objects.count()}クラス"),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"生徒: {User.objects.filter(username__startswith='student_').count()}名",
            ),
        )

import random
from datetime import datetime
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from school_diary.diary.models import DiaryEntry

User = get_user_model()


class Command(BaseCommand):
    help = "過去30日分のサンプル連絡帳データを作成"

    def handle(self, *args, **options):
        students = User.objects.filter(username__startswith="student_")
        teachers = User.objects.filter(username__startswith="teacher_")

        if not students.exists():
            self.stdout.write(
                self.style.ERROR("❌ 先に create_test_users を実行してください"),
            )
            return

        entries = []
        today = timezone.now().date()

        # サンプル振り返り文
        reflections = [
            "今日は数学のテストがありました。結果が楽しみです。",
            "部活で新しい技を覚えました。練習頑張ります。",
            "友達と遊んで楽しかったです。",
            "宿題が多くて大変でした。",
            "体育祭の準備をしました。本番が楽しみです。",
            "英語の授業が面白かったです。",
            "今日は図書館で勉強しました。",
            "野球部の練習で良いプレーができました。",
            "文化祭の準備が楽しいです。",
            "今日は少し疲れました。明日は早く寝ます。",
            "友達と一緒にプロジェクトを進めました。",
            "理科の実験が面白かったです。",
            "新しい友達ができました。",
            "今日のランチがとても美味しかったです。",
            "放課後に友達と勉強しました。",
        ]

        for student in students:
            for days_ago in range(30):
                entry_date = today - timedelta(days=days_ago + 1)

                # 80%の確率でデータ作成（提出漏れを再現）
                if random.random() < 0.8:
                    # 体調・メンタルは正規分布に近い分布（3が最も多い）
                    health = random.choices(
                        [1, 2, 3, 4, 5],
                        weights=[5, 10, 50, 25, 10],
                    )[0]
                    mental = random.choices(
                        [1, 2, 3, 4, 5],
                        weights=[5, 10, 50, 25, 10],
                    )[0]

                    submission_datetime = timezone.make_aware(
                        datetime.combine(
                            entry_date + timedelta(days=1),
                            datetime.min.time().replace(
                                hour=random.randint(7, 9),
                                minute=random.randint(0, 59),
                            ),
                        ),
                    )

                    entry = DiaryEntry(
                        student=student,
                        entry_date=entry_date,
                        health_condition=health,
                        mental_condition=mental,
                        reflection=random.choice(reflections),
                        submission_date=submission_datetime,
                    )

                    # 70%の確率で既読処理
                    if random.random() < 0.7:
                        entry.is_read = True
                        entry.read_by = random.choice(teachers)
                        entry.read_at = submission_datetime + timedelta(
                            hours=random.randint(1, 8),
                        )

                    entries.append(entry)

        # 一括作成（パフォーマンス最適化）
        DiaryEntry.objects.bulk_create(entries, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(
            self.style.SUCCESS(f"✅ {len(entries)}件の連絡帳データを作成しました"),
        )
        self.stdout.write(self.style.SUCCESS("期間: 過去30日分"))
        self.stdout.write(self.style.SUCCESS(f"生徒数: {students.count()}名"))

        # 統計情報
        total_entries = DiaryEntry.objects.count()
        read_entries = DiaryEntry.objects.filter(is_read=True).count()
        unread_entries = DiaryEntry.objects.filter(is_read=False).count()

        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("📊 統計情報"))
        self.stdout.write(self.style.SUCCESS(f"総エントリ数: {total_entries}件"))
        self.stdout.write(
            self.style.SUCCESS(
                f"既読: {read_entries}件（{read_entries / total_entries * 100:.1f}%）",
            ),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"未読: {unread_entries}件（{unread_entries / total_entries * 100:.1f}%）",
            ),
        )

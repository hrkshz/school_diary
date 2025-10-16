#!/usr/bin/env python
"""アラート機能QAテスト用データ作成スクリプト

このスクリプトは、アラート機能の全パターンをテストするためのデータを作成します。

テストケース:
- TC-A1: メンタル★1（Critical Alert）
- TC-B1: 3日連続メンタル★1（Escalation Alert）
- TC-C1: 連続低下パターン（Warning Alert）
- TC-D1: クラス5人以上体調不良（Class Health Alert）
- TC-E1: 未提出生徒（Student Reminder）
"""

import os
import sys
import django
from datetime import date, timedelta

# Django設定
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from school_diary.diary.models import DiaryEntry, ClassRoom

User = get_user_model()

def create_alert_test_data():
    """アラート機能テストデータ作成"""

    print("=" * 60)
    print("アラート機能QAテストデータ作成")
    print("=" * 60)

    # 既存のDiaryEntryを削除（クリーンな状態で開始）
    DiaryEntry.objects.all().delete()
    print("✅ 既存の連絡帳データを削除")

    # 1年A組の生徒を取得
    classroom_1a = ClassRoom.objects.get(grade=1, class_name="A", academic_year=2025)
    students = list(classroom_1a.students.all().order_by('id')[:5])

    if len(students) < 5:
        print("❌ エラー: 1年A組の生徒が5名未満です")
        return

    # 固定日付（テストと同じ）
    date1 = date(2025, 10, 13)  # 月曜日
    date2 = date(2025, 10, 14)  # 火曜日
    date3 = date(2025, 10, 15)  # 水曜日

    print(f"\n日付範囲: {date1} 〜 {date3}")
    print(f"対象クラス: {classroom_1a}")
    print(f"対象生徒数: {len(students)}名\n")

    # student_001: TC-A1（メンタル★1 - Critical Alert） + TC-D1（体調不良）
    student_001 = students[0]
    # 過去データ（パターン: 1→2→1 で連続低下を回避）
    DiaryEntry.objects.create(
        student=student_001,
        entry_date=date1,
        health_condition=4,
        mental_condition=1,  # ★1
        reflection="少し辛いです。",
    )
    DiaryEntry.objects.create(
        student=student_001,
        entry_date=date2,
        health_condition=4,
        mental_condition=2,  # ★★（回復傾向）
        reflection="少し良くなりました。",
    )
    # 本日（メンタル★1 + 体調★1 = 両方のアラート対象）
    DiaryEntry.objects.create(
        student=student_001,
        entry_date=date3,
        health_condition=1,  # 体調不良（TC-D1用 1/5）
        mental_condition=1,  # ★1 → Critical Alert（連続低下なし: 1→2→1）
        reflection="最近、学校に行くのが辛いです。体調も悪いです。",
    )
    print(f"✅ {student_001.username}: メンタル★1 (Critical Alert, 連続低下なし) + 体調不良 ★ (Class Health Alert用 1/5)")

    # student_002: TC-B1（3日連続メンタル★1 - Escalation Alert） + TC-D1（体調不良）
    student_002 = students[1]
    for i, d in enumerate([date1, date2, date3], 1):
        # 最終日（date3）のみ体調不良を追加
        health_val = 2 if d == date3 else 3
        DiaryEntry.objects.create(
            student=student_002,
            entry_date=d,
            health_condition=health_val,  # 最終日のみ体調不良
            mental_condition=1,  # 3日連続★1 → Escalation Alert
            reflection=f"Day {i}: とても辛い状態が続いています。",
        )
    print(f"✅ {student_002.username}: 3日連続メンタル★1 (Escalation Alert) + 体調不良 ★★ (Class Health Alert用 2/5)")

    # student_003: TC-C1（連続低下パターン 5→4→3 - Warning Alert） + TC-D1（体調不良）
    student_003 = students[2]
    for i, (d, mental_val) in enumerate(zip([date1, date2, date3], [5, 4, 3]), 1):
        # 最終日（date3）のみ体調不良を追加
        health_val = 2 if d == date3 else 4
        DiaryEntry.objects.create(
            student=student_003,
            entry_date=d,
            health_condition=health_val,  # 最終日のみ体調不良
            mental_condition=mental_val,  # 5→4→3 → Warning Alert
            reflection=f"Day {i}: 少しずつ調子が悪くなっています。",
        )
    print(f"✅ {student_003.username}: メンタル連続低下 5→4→3 (Warning Alert) + 体調不良 ★★ (Class Health Alert用 3/5)")

    # student_004, 005: 過去は正常、最終日のみ体調不良（TC-D1用 4/5, 5/5）
    for i, student in enumerate([students[3], students[4]], 4):
        for d in [date1, date2, date3]:
            # 最終日（date3）のみ体調不良を追加
            health_val = 2 if d == date3 else 4
            DiaryEntry.objects.create(
                student=student,
                entry_date=d,
                health_condition=health_val,  # 最終日のみ体調不良
                mental_condition=4,  # 正常
                reflection="元気です。" if d != date3 else "少し体調が悪いです。",
            )
        print(f"✅ {student.username}: 最終日体調不良 ★★ (Class Health Alert用 {i}/5)")

    # 1年B組から3名取得（別のテスト用）
    classroom_1b = ClassRoom.objects.get(grade=1, class_name="B", academic_year=2025)
    students_1b = list(classroom_1b.students.all().order_by('id'))

    # 1年B組の生徒にもデータ作成（1年B組の担任のテスト用）
    for i, student in enumerate(students_1b[:3], 1):
        DiaryEntry.objects.create(
            student=student,
            entry_date=date3,
            health_condition=2,  # 体調不良
            mental_condition=3,
            reflection=f"体調不良です（1年B組）",
        )
        print(f"✅ {student.username}: 体調不良 ★★ (1年B組データ)")

    print(f"\n✅ 1年A組の体調不良: 5名（student_001, 002, 003, 004, 005 の最終日）→ Class Health Alert表示")

    # TC-E1: 未提出生徒（student_006 = 1年B組の4人目）
    # 何もデータを作らない → 未提出 → Student Reminder表示
    if len(classroom_1b.students.all()) >= 4:
        student_no_entry = list(classroom_1b.students.all().order_by('id'))[3]
        print(f"\n✅ {student_no_entry.username}: 未提出（Student Reminder表示）")

    print("\n" + "=" * 60)
    print("テストデータ作成完了")
    print("=" * 60)
    print("\n📊 作成データサマリー:")
    print(f"  - 連絡帳エントリー: {DiaryEntry.objects.count()}件")
    print(f"  - 対象生徒: {len(students) + len(students_1b)}名")
    print(f"  - 対象クラス: 1年A組 + 1年B組")
    print("\n🎯 期待されるアラート:")
    print("  1. ✅ Critical Alert: 1件（student_001）")
    print("  2. ✅ Escalation Alert: 1件（student_002、学年主任へ）")
    print("  3. ✅ Warning Alert（メンタル低下）: 1件（student_003）")
    print("  4. ✅ Warning Alert（クラス体調不良）: 1件（5名以上）")
    print("  5. ✅ Student Reminder: 対象生徒のみ表示")
    print("\n🔗 確認URL:")
    print("  - 担任ダッシュボード: http://localhost:8000/ (teacher_1_a@example.com)")
    print("  - 学年主任ダッシュボード: http://localhost:8000/diary/grade-overview/")
    print("  - 生徒ダッシュボード: http://localhost:8000/ (student_006@example.com)")
    print("=" * 60)

if __name__ == "__main__":
    create_alert_test_data()

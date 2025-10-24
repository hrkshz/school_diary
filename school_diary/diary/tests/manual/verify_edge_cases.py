#!/usr/bin/env python
"""エッジケース・ネガティブテスト検証スクリプト

QA Phase 4のテストケースを自動検証します。
"""

import os
import sys
from datetime import date

import django

# Django設定
sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.contrib.auth import get_user_model

from school_diary.diary.models import ClassRoom
from school_diary.diary.models import DiaryEntry
from school_diary.diary.utils import check_consecutive_decline
from school_diary.diary.utils import check_critical_mental_state

User = get_user_model()

def verify_bva_tests():
    """境界値テスト（BVA）の検証"""

    print("=" * 70)
    print("🔍 BVA Tests: 境界値テスト検証")
    print("=" * 70)

    test_results = []
    date3 = date(2025, 10, 15)

    # BVA-1: クラス体調不良の閾値テスト
    print("\n📌 BVA-1: クラス体調不良の閾値テスト")

    classroom_1b = ClassRoom.objects.get(grade=1, class_name="B", academic_year=2025)

    poor_health_count = DiaryEntry.objects.filter(
        student__classes=classroom_1b,
        entry_date=date3,
        health_condition__lte=2,
    ).count()

    # BVA-1B: 5名体調不良 → アラートあり
    expected_alert = poor_health_count >= 5
    result_bva1 = expected_alert == True
    test_results.append(result_bva1)

    print(f"  BVA-1B: 1-B組の体調不良 {poor_health_count}名")
    print("  期待: アラートあり（5名以上）")
    print(f"  実際: アラート{'あり' if expected_alert else 'なし'}")
    print(f"  結果: {'✅ PASS' if result_bva1 else '❌ FAIL'}")

    # BVA-2: メンタル連続低下の日数テスト
    print("\n📌 BVA-2: メンタル連続低下の日数テスト")

    classroom_2a = ClassRoom.objects.get(grade=2, class_name="A", academic_year=2025)
    students_2a = list(classroom_2a.students.all().order_by("id"))

    # BVA-2A: 2日連続低下 → アラートなし
    student_2a_1 = students_2a[0]
    decline_2a_1 = check_consecutive_decline(student_2a_1, "mental_condition")
    result_bva2a = decline_2a_1["has_alert"] == False
    test_results.append(result_bva2a)

    print(f"  BVA-2A: {student_2a_1.username} (2日連続)")
    print("  期待: アラートなし")
    print(f"  実際: アラート{'あり' if decline_2a_1['has_alert'] else 'なし'}")
    print(f"  結果: {'✅ PASS' if result_bva2a else '❌ FAIL'}")

    # BVA-2B: 3日連続低下 → アラートあり
    student_2a_2 = students_2a[1]
    decline_2a_2 = check_consecutive_decline(student_2a_2, "mental_condition")
    result_bva2b = decline_2a_2["has_alert"] == True
    test_results.append(result_bva2b)

    print(f"  BVA-2B: {student_2a_2.username} (3日連続)")
    print("  期待: アラートあり")
    print(f"  実際: アラート{'あり' if decline_2a_2['has_alert'] else 'なし'}")
    if decline_2a_2["has_alert"]:
        print(f"  推移: {decline_2a_2['trend']}")
    print(f"  結果: {'✅ PASS' if result_bva2b else '❌ FAIL'}")

    # BVA-2C: 4日連続低下 → アラートあり（最新3日を評価）
    student_2a_3 = students_2a[2]
    decline_2a_3 = check_consecutive_decline(student_2a_3, "mental_condition")
    result_bva2c = decline_2a_3["has_alert"] == True
    test_results.append(result_bva2c)

    print(f"  BVA-2C: {student_2a_3.username} (4日連続、最新3日評価)")
    print("  期待: アラートあり（最新3日: 4→3→2）")
    print(f"  実際: アラート{'あり' if decline_2a_3['has_alert'] else 'なし'}")
    if decline_2a_3["has_alert"]:
        print(f"  推移: {decline_2a_3['trend']}")
    print(f"  結果: {'✅ PASS' if result_bva2c else '❌ FAIL'}")

    return test_results

def verify_negative_tests():
    """ネガティブテスト（NEG）の検証"""

    print("\n" + "=" * 70)
    print("🔍 NEG Tests: ネガティブテスト検証")
    print("=" * 70)

    test_results = []

    classroom_2a = ClassRoom.objects.get(grade=2, class_name="A", academic_year=2025)
    students_2a = list(classroom_2a.students.all().order_by("id"))

    classroom_2b = ClassRoom.objects.get(grade=2, class_name="B", academic_year=2025)
    students_2b = list(classroom_2b.students.all().order_by("id"))

    classroom_3a = ClassRoom.objects.get(grade=3, class_name="A", academic_year=2025)
    students_3a = list(classroom_3a.students.all().order_by("id"))

    # NEG-1: 非連続パターン
    print("\n📌 NEG-1: 非連続パターン（アラート非表示確認）")

    # NEG-1A: V字回復（1→5→1）
    student_neg1a = students_2a[3]
    decline_neg1a = check_consecutive_decline(student_neg1a, "mental_condition")
    result_neg1a = decline_neg1a["has_alert"] == False
    test_results.append(result_neg1a)

    print(f"  NEG-1A: {student_neg1a.username} (V字回復 1→5→1)")
    print("  期待: アラートなし")
    print(f"  実際: アラート{'あり' if decline_neg1a['has_alert'] else 'なし'}")
    print(f"  結果: {'✅ PASS' if result_neg1a else '❌ FAIL'}")

    # NEG-1B: 一時的低下（5→3→5）
    student_neg1b = students_2a[4]
    decline_neg1b = check_consecutive_decline(student_neg1b, "mental_condition")
    result_neg1b = decline_neg1b["has_alert"] == False
    test_results.append(result_neg1b)

    print(f"  NEG-1B: {student_neg1b.username} (一時的低下 5→3→5)")
    print("  期待: アラートなし")
    print(f"  実際: アラート{'あり' if decline_neg1b['has_alert'] else 'なし'}")
    print(f"  結果: {'✅ PASS' if result_neg1b else '❌ FAIL'}")

    # NEG-1C: 横ばい（3→3→3）
    student_neg1c = students_2b[0]
    decline_neg1c = check_consecutive_decline(student_neg1c, "mental_condition")
    result_neg1c = decline_neg1c["has_alert"] == False
    test_results.append(result_neg1c)

    print(f"  NEG-1C: {student_neg1c.username} (横ばい 3→3→3)")
    print("  期待: アラートなし")
    print(f"  実際: アラート{'あり' if decline_neg1c['has_alert'] else 'なし'}")
    print(f"  結果: {'✅ PASS' if result_neg1c else '❌ FAIL'}")

    # NEG-2: データ欠損パターン
    print("\n📌 NEG-2: データ欠損パターン")

    # NEG-2A: 0日分
    student_neg2a = students_2b[1]
    decline_neg2a = check_consecutive_decline(student_neg2a, "mental_condition")
    critical_neg2a = check_critical_mental_state(student_neg2a)
    result_neg2a = (decline_neg2a["has_alert"] == False and critical_neg2a["has_alert"] == False)
    test_results.append(result_neg2a)

    print(f"  NEG-2A: {student_neg2a.username} (0日分)")
    print("  期待: 全アラートなし")
    print(f"  実際: 連続低下={'あり' if decline_neg2a['has_alert'] else 'なし'}, Critical={'あり' if critical_neg2a['has_alert'] else 'なし'}")
    print(f"  結果: {'✅ PASS' if result_neg2a else '❌ FAIL'}")

    # NEG-2B: 1日分のみ
    student_neg2b = students_2b[2]
    decline_neg2b = check_consecutive_decline(student_neg2b, "mental_condition")
    critical_neg2b = check_critical_mental_state(student_neg2b)
    result_neg2b = (decline_neg2b["has_alert"] == False and critical_neg2b["has_alert"] == True)  # Critical★1なので表示される
    test_results.append(result_neg2b)

    print(f"  NEG-2B: {student_neg2b.username} (1日分のみ, mental=1)")
    print("  期待: 連続低下なし、Criticalあり（★1なので）")
    print(f"  実際: 連続低下={'あり' if decline_neg2b['has_alert'] else 'なし'}, Critical={'あり' if critical_neg2b['has_alert'] else 'なし'}")
    print(f"  結果: {'✅ PASS' if result_neg2b else '❌ FAIL'}")

    # NEG-2C: 2日分のみ
    student_neg2c = students_2b[3]
    decline_neg2c = check_consecutive_decline(student_neg2c, "mental_condition")
    result_neg2c = decline_neg2c["has_alert"] == False
    test_results.append(result_neg2c)

    print(f"  NEG-2C: {student_neg2c.username} (2日分のみ)")
    print("  期待: アラートなし")
    print(f"  実際: アラート{'あり' if decline_neg2c['has_alert'] else 'なし'}")
    print(f"  結果: {'✅ PASS' if result_neg2c else '❌ FAIL'}")

    # NEG-3: 土日を挟むパターン
    print("\n📌 NEG-3: 土日を挟むパターン")

    # NEG-3A: 金月火（5→4→3、土日挟む）→ アラートあり
    student_neg3a = students_2b[4]
    decline_neg3a = check_consecutive_decline(student_neg3a, "mental_condition")
    result_neg3a = decline_neg3a["has_alert"] == True
    test_results.append(result_neg3a)

    print(f"  NEG-3A: {student_neg3a.username} (金月火 5→4→3、土日挟む)")
    print("  期待: アラートあり")
    print(f"  実際: アラート{'あり' if decline_neg3a['has_alert'] else 'なし'}")
    if decline_neg3a["has_alert"]:
        print(f"  推移: {decline_neg3a['trend']}")
    print(f"  結果: {'✅ PASS' if result_neg3a else '❌ FAIL'}")

    # NEG-3B: 金月（2件のみ、土日挟む）→ アラートなし
    student_neg3b = students_3a[0]
    decline_neg3b = check_consecutive_decline(student_neg3b, "mental_condition")
    result_neg3b = decline_neg3b["has_alert"] == False
    test_results.append(result_neg3b)

    print(f"  NEG-3B: {student_neg3b.username} (金月 5→4、2日のみ)")
    print("  期待: アラートなし")
    print(f"  実際: アラート{'あり' if decline_neg3b['has_alert'] else 'なし'}")
    print(f"  結果: {'✅ PASS' if result_neg3b else '❌ FAIL'}")

    return test_results

def verify_isolation_tests():
    """分離テスト（ISO）の検証"""

    print("\n" + "=" * 70)
    print("🔍 ISO Tests: 分離テスト検証")
    print("=" * 70)

    test_results = []

    # ISO-3: 学年横断エスカレーション
    print("\n📌 ISO-3: 学年横断エスカレーション")

    # 1年学年主任
    grade_leader = User.objects.get(username="teacher_1_a@example.com")
    managed_grade = grade_leader.profile.managed_grade

    # 1年生の全クラスを取得
    classrooms_grade1 = ClassRoom.objects.filter(
        grade=managed_grade,
        academic_year=2025,
    ).prefetch_related("students")

    escalation_alerts_grade1 = []

    for classroom in classrooms_grade1:
        for student in classroom.students.all():
            recent_entries = student.diary_entries.order_by("-entry_date")[:3]

            if len(recent_entries) == 3 and all(
                entry.mental_condition == 1 for entry in recent_entries
            ):
                escalation_alerts_grade1.append({
                    "student": student,
                    "classroom": classroom,
                })

    # ISO-3A: 1-B組のstudent_006が表示されるか
    classroom_1b = ClassRoom.objects.get(grade=1, class_name="B", academic_year=2025)
    students_1b = list(classroom_1b.students.all().order_by("id"))
    student_1b_escalation = students_1b[0]  # student_006

    found_1b = any(alert["student"] == student_1b_escalation for alert in escalation_alerts_grade1)
    result_iso3a = found_1b == True
    test_results.append(result_iso3a)

    print(f"  ISO-3A: {student_1b_escalation.username} (1-B組)")
    print("  期待: 学年主任に表示される")
    print(f"  実際: {'表示される' if found_1b else '表示されない'}")
    print(f"  結果: {'✅ PASS' if result_iso3a else '❌ FAIL'}")

    # ISO-3B: 2-A組の生徒が表示されないか
    classroom_2a = ClassRoom.objects.get(grade=2, class_name="A", academic_year=2025)
    students_2a = list(classroom_2a.students.all().order_by("id"))
    student_2a_escalation = students_2a[3]  # NEG-1Aを上書きしたstudent

    found_2a = any(alert["student"] == student_2a_escalation for alert in escalation_alerts_grade1)
    result_iso3b = found_2a == False  # 2年生なので1年学年主任には表示されない
    test_results.append(result_iso3b)

    print(f"  ISO-3B: {student_2a_escalation.username} (2-A組)")
    print("  期待: 1年学年主任に表示されない（2年生のため）")
    print(f"  実際: {'表示される' if found_2a else '表示されない'}")
    print(f"  結果: {'✅ PASS' if result_iso3b else '❌ FAIL'}")

    print(f"\n  1年学年主任に表示されるエスカレーションアラート: {len(escalation_alerts_grade1)}件")
    for alert in escalation_alerts_grade1:
        print(f"    - {alert['student'].username} ({alert['classroom']})")

    return test_results

def main():
    """メイン検証フロー"""

    print("\n")
    print("=" * 70)
    print("🎯 QA Phase 4: エッジケース・ネガティブテスト検証")
    print("=" * 70)
    print("\n")

    all_results = []

    # 1. BVA Tests
    results_bva = verify_bva_tests()
    all_results.extend(results_bva)

    # 2. NEG Tests
    results_neg = verify_negative_tests()
    all_results.extend(results_neg)

    # 3. ISO Tests
    results_iso = verify_isolation_tests()
    all_results.extend(results_iso)

    # 総合結果
    total_tests = len(all_results)
    passed_tests = sum(all_results)
    failed_tests = total_tests - passed_tests

    print("\n" + "=" * 70)
    print("📊 QA Phase 4検証結果サマリー")
    print("=" * 70)
    print(f"\n総テスト数: {total_tests}件")
    print(f"✅ PASS: {passed_tests}件")
    print(f"❌ FAIL: {failed_tests}件")
    print(f"合格率: {(passed_tests/total_tests*100):.1f}%\n")

    if failed_tests == 0:
        print("🎉 全テストPASS！エッジケース・ネガティブテストは完璧です。")
    else:
        print("⚠️  一部のテストがFAILしました。詳細を確認してください。")

    print("=" * 70)
    print()

if __name__ == "__main__":
    main()

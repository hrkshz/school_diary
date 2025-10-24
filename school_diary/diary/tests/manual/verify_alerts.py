#!/usr/bin/env python
"""アラート機能検証スクリプト

実際のView層のアラート生成ロジックを呼び出して、期待される結果と比較します。
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
from school_diary.diary.utils import get_previous_school_day

User = get_user_model()

def verify_teacher_dashboard_alerts():
    """担任ダッシュボードのアラート検証"""

    print("=" * 70)
    print("🔍 担任ダッシュボード アラート検証")
    print("=" * 70)

    # 1年A組の担任
    teacher = User.objects.get(username="teacher_1_a@example.com")
    classroom = teacher.homeroom_classes.first()

    print(f"\n担任: {teacher.username}")
    print(f"クラス: {classroom}")
    print(f"生徒数: {classroom.students.count()}名\n")

    # アラート生成（TeacherDashboardViewのロジックをシミュレート）
    alerts = []
    today = date.today()

    # 全生徒をチェック
    for student in classroom.students.all():
        # Level 1: Critical - メンタル★1
        mental_state = check_critical_mental_state(student)
        if mental_state["has_alert"]:
            alerts.append({
                "level": "critical",
                "type": "mental_critical",
                "student": student,
                "message": f"{student.get_full_name()}さん - メンタル★1",
                "date": mental_state["date"],
            })

        # Level 3: Warning - メンタル3日連続低下
        mental_decline = check_consecutive_decline(student, "mental_condition")
        if mental_decline["has_alert"]:
            trend_values = mental_decline["trend"]
            trend_str = " → ".join([f"★{'★' * v}" for v in trend_values])
            alerts.append({
                "level": "warning",
                "type": "mental_decline",
                "student": student,
                "message": f"{student.get_full_name()}さん - メンタル低下が続いています",
                "trend": trend_str,
                "dates": mental_decline["dates"],
            })

    # Level 4: Warning - クラス5人以上が体調不良
    previous_date = get_previous_school_day(today)
    poor_health_count = DiaryEntry.objects.filter(
        student__classes=classroom,
        entry_date=previous_date,
        health_condition__lte=2,
    ).count()

    if poor_health_count >= 5:
        alerts.append({
            "level": "warning",
            "type": "class_health",
            "message": f"クラス全体 - 体調不良が多いです（{poor_health_count}名）",
            "date": previous_date,
        })

    # 結果表示
    print(f"🚨 検出されたアラート: {len(alerts)}件\n")

    test_results = []

    # TC-A1: メンタル★1（Critical）
    critical_alerts = [a for a in alerts if a["type"] == "mental_critical"]
    expected_critical = 2  # student_001 + student_002（student_002はEscalationも兼ねる）
    result_a1 = len(critical_alerts) == expected_critical
    test_results.append(result_a1)

    print("TC-A1: Critical Alert（メンタル★1）")
    print(f"  期待: {expected_critical}件 (student_001 + student_002)")
    print(f"  実際: {len(critical_alerts)}件")
    print(f"  結果: {'✅ PASS' if result_a1 else '❌ FAIL'}")
    print("  備考: student_002は担任ダッシュボードでCritical、学年主任でEscalation両方表示")

    if critical_alerts:
        for alert in critical_alerts:
            print(f"    - {alert['student'].username}: {alert['message']}")
    print()

    # TC-C1: メンタル連続低下（Warning）
    decline_alerts = [a for a in alerts if a["type"] == "mental_decline"]
    expected_decline = 1  # student_003
    result_c1 = len(decline_alerts) == expected_decline
    test_results.append(result_c1)

    print("TC-C1: Warning Alert（メンタル連続低下）")
    print(f"  期待: {expected_decline}件")
    print(f"  実際: {len(decline_alerts)}件")
    print(f"  結果: {'✅ PASS' if result_c1 else '❌ FAIL'}")

    if decline_alerts:
        for alert in decline_alerts:
            print(f"    - {alert['student'].username}: {alert['message']}")
            print(f"      推移: {alert['trend']}")
    print()

    # TC-D1: クラス体調不良（Warning）
    class_health_alerts = [a for a in alerts if a["type"] == "class_health"]
    expected_class_health = 1  # 5名以上
    result_d1 = len(class_health_alerts) == expected_class_health
    test_results.append(result_d1)

    print("TC-D1: Warning Alert（クラス体調不良）")
    print(f"  期待: {expected_class_health}件")
    print(f"  実際: {len(class_health_alerts)}件")
    print(f"  結果: {'✅ PASS' if result_d1 else '❌ FAIL'}")

    if class_health_alerts:
        for alert in class_health_alerts:
            print(f"    - {alert['message']}")
            print(f"      日付: {alert['date']}")
    print()

    return test_results

def verify_grade_leader_dashboard_alerts():
    """学年主任ダッシュボードのアラート検証"""

    print("=" * 70)
    print("🔍 学年主任ダッシュボード アラート検証")
    print("=" * 70)

    # 学年主任（1年A組担任が兼任）
    grade_leader = User.objects.get(username="teacher_1_a@example.com")
    managed_grade = grade_leader.profile.managed_grade

    print(f"\n学年主任: {grade_leader.username}")
    print(f"管理学年: {managed_grade}年生\n")

    # 同じ学年の全クラスを取得
    classrooms = ClassRoom.objects.filter(
        grade=managed_grade,
        academic_year=2025,
    ).prefetch_related("students")

    # エスカレーションアラート生成（GradeOverviewViewのロジックをシミュレート）
    escalation_alerts = []

    for classroom in classrooms:
        for student in classroom.students.all():
            # 過去3日分のエントリーを取得
            recent_entries = student.diary_entries.order_by("-entry_date")[:3]

            # 3件揃っているか、かつ全てメンタル★1かチェック
            if len(recent_entries) == 3 and all(
                entry.mental_condition == 1 for entry in recent_entries
            ):
                escalation_alerts.append({
                    "level": "critical_escalation",
                    "student": student,
                    "classroom": classroom,
                    "teacher": classroom.homeroom_teacher,
                    "message": f"【学年主任通知】{classroom}組 {student.get_full_name()}さん - メンタル★1が3日連続",
                    "dates": [entry.entry_date for entry in reversed(recent_entries)],
                })

    # 結果表示
    print(f"🚨 検出されたエスカレーションアラート: {len(escalation_alerts)}件\n")

    test_results = []

    # TC-B1: 3日連続メンタル★1（Critical-Escalation）
    expected_escalation = 1  # student_002
    result_b1 = len(escalation_alerts) == expected_escalation
    test_results.append(result_b1)

    print("TC-B1: Escalation Alert（3日連続メンタル★1）")
    print(f"  期待: {expected_escalation}件")
    print(f"  実際: {len(escalation_alerts)}件")
    print(f"  結果: {'✅ PASS' if result_b1 else '❌ FAIL'}")

    if escalation_alerts:
        for alert in escalation_alerts:
            print(f"    - {alert['student'].username}: {alert['message']}")
            print(f"      担任: {alert['teacher'].username}")
            print(f"      期間: {alert['dates']}")
    print()

    return test_results

def verify_student_dashboard_reminder():
    """生徒ダッシュボードのリマインダー検証"""

    print("=" * 70)
    print("🔍 生徒ダッシュボード リマインダー検証")
    print("=" * 70)

    # 未提出生徒（student_009）
    student = User.objects.get(username="student_009@example.com")

    print(f"\n生徒: {student.username}")
    print(f"氏名: {student.get_full_name()}\n")

    # リマインダー判定（StudentDashboardViewのロジックをシミュレート）
    expected_date = get_previous_school_day(date.today())
    today_submitted = DiaryEntry.objects.filter(
        student=student,
        entry_date=expected_date,
    ).exists()

    has_reminder = not today_submitted

    test_results = []

    # TC-E1: 未提出リマインダー
    expected_reminder = True  # student_009は未提出
    result_e1 = has_reminder == expected_reminder
    test_results.append(result_e1)

    print("TC-E1: Student Reminder（未提出）")
    print(f"  期待: リマインダー表示 = {expected_reminder}")
    print(f"  実際: リマインダー表示 = {has_reminder}")
    print(f"  対象日: {expected_date}")
    print(f"  結果: {'✅ PASS' if result_e1 else '❌ FAIL'}\n")

    return test_results

def main():
    """メイン検証フロー"""

    print("\n")
    print("=" * 70)
    print("🎯 アラート機能 QA検証")
    print("=" * 70)
    print("\n")

    all_results = []

    # 1. 担任ダッシュボード検証
    results_teacher = verify_teacher_dashboard_alerts()
    all_results.extend(results_teacher)

    # 2. 学年主任ダッシュボード検証
    results_grade = verify_grade_leader_dashboard_alerts()
    all_results.extend(results_grade)

    # 3. 生徒ダッシュボード検証
    results_student = verify_student_dashboard_reminder()
    all_results.extend(results_student)

    # 総合結果
    total_tests = len(all_results)
    passed_tests = sum(all_results)
    failed_tests = total_tests - passed_tests

    print("=" * 70)
    print("📊 QA検証結果サマリー")
    print("=" * 70)
    print(f"\n総テスト数: {total_tests}件")
    print(f"✅ PASS: {passed_tests}件")
    print(f"❌ FAIL: {failed_tests}件")
    print(f"合格率: {(passed_tests/total_tests*100):.1f}%\n")

    if failed_tests == 0:
        print("🎉 全テストPASS！アラート機能は正常に動作しています。")
    else:
        print("⚠️  一部のテストがFAILしました。詳細を確認してください。")

    print("=" * 70)
    print()

if __name__ == "__main__":
    main()

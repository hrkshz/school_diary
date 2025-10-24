# 要件トレーサビリティマトリックス

> **作成日**: 2025-10-23
> **対象**: 連絡帳管理システム v0.3.0-map
> **目的**: 要件と単体テストのマッピング

---

## トレーサビリティマトリックスとは

要件定義書の各要件が、どのテストでカバーされているかを示す表。

**目的**:
- 要件漏れの検出
- テストの妥当性確認
- リグレッションテスト範囲の特定

---

## 必須機能（課題1）のトレーサビリティ

| 要件ID | 要件名 | テストファイル | テスト名 | カバレッジ | 状態 |
|--------|--------|--------------|---------|----------|------|
| **T-01** | **連絡帳閲覧** | test_ui.py | test_student_health_mental_displayed | 正常系のみ | ⚠️ 不足 |
| | | test_teacher_dashboard_service.py | test_get_classroom_summary_with_unread_entries | 正常系 | ⚠️ 不足 |
| **T-02** | **既読処理** | test_ui.py | test_mark_as_read_with_reaction_only | 正常系 | ✅ |
| | | test_ui.py | test_mark_as_read_with_reaction_and_action | 正常系 | ✅ |
| | | test_ui.py | test_update_reaction_after_read | 更新ロジック | ✅ |
| | | test_ui.py | test_update_action_after_read | 更新ロジック | ✅ |
| | | test_ui.py | test_change_reaction_after_read | 変更ロジック | ✅ |
| | | test_ui.py | test_change_action_after_read | 変更ロジック | ✅ |
| | | test_ui.py | test_remove_action_after_read | 削除ロジック | ✅ |
| | | test_ui.py | test_action_status_management | ステータス管理 | ✅ |
| **T-03** | **提出状況確認** | test_teacher_dashboard_service.py | test_get_classroom_summary_empty | 正常系 | ⚠️ 不足 |
| | | test_teacher_dashboard_service.py | test_get_classroom_summary_with_unread_entries | 正常系 | ⚠️ 不足 |
| | | test_alert_service.py | test_classify_not_submitted | 未提出検出 | ✅ |
| **T-04** | **過去記録閲覧** | test_ui.py | test_table_exists_with_data | UI表示 | ⚠️ 不足 |
| | | test_ui.py | test_entry_displayed_with_badges | UI表示 | ⚠️ 不足 |
| **S-01** | **連絡帳作成** | test_diary_entry_service.py | test_create_entry_auto_sets_classroom | 正常系 | ✅ |
| | | test_diary_entry_service.py | test_create_entry_with_explicit_classroom | 正常系 | ✅ |
| | | test_diary_entry_service.py | test_create_entry_initializes_action_status_not_required | 初期化ロジック | ✅ |
| | | test_diary_entry_service.py | test_create_entry_with_internal_action_sets_pending | ステータスロジック | ✅ |
| | | test_model_validation.py | test_completed_with_all_fields_passes | バリデーション | ✅ |
| **S-02** | **連絡帳編集（既読前のみ）** | - | **テスト不足** | - | ❌ **Critical Gap** |
| **S-03** | **過去記録閲覧** | test_ui.py | test_table_exists_with_data | UI表示 | ⚠️ 不足 |
| **A-01** | **ユーザー作成** | test_admin_user_creation.py | test_student_creation | 正常系 | ✅ |
| | | test_admin_user_creation.py | test_teacher_creation | 正常系 | ✅ |
| | | test_admin_user_creation.py | test_grade_leader_creation | 正常系 | ✅ |
| | | test_admin_user_creation.py | test_school_leader_creation | 正常系 | ✅ |
| | | test_admin_user_creation.py | test_admin_user_creation | 正常系 | ✅ |
| | | test_admin_user_creation.py | test_duplicate_email | 異常系 | ✅ |
| **A-02** | **クラス管理** | test_classroom_admin.py | test_classroom_has_assistant_teachers_field | フィールド確認 | ⚠️ 不足 |
| **A-03** | **割り当て管理** | test_admin_user_creation.py | test_student_classroom_assignment | 生徒割り当て | ✅ |
| | | test_admin_user_creation.py | test_teacher_classroom_assignment | 担任割り当て | ✅ |

---

## 改善機能（課題2）のトレーサビリティ

| 要件ID | 要件名 | テストファイル | テスト名 | カバレッジ | 状態 |
|--------|--------|--------------|---------|----------|------|
| **E-01** | **体調・メンタル数値化** | test_model_validation.py | (models.py 95%カバー) | 正常系+バリデーション | ✅ |
| **E-04** | **教師間メモ機能** | test_ui.py | test_notes_displayed_with_correct_badges | 正常系 | ✅ |
| | | test_ui.py | test_edit_delete_buttons_only_for_creator | 権限チェック | ✅ |
| | | test_ui.py | test_shared_notes_visible_to_other_teachers | 共有ロジック | ✅ |
| | | test_ui.py | test_edit_note_modal_preloaded | 編集機能 | ✅ |
| **E-08** | **アラート機能** | test_alert_service.py | test_classify_important_mental_star_1 | P0検出 | ✅ |
| | | test_alert_service.py | test_classify_needs_attention_3day_decline | P1検出 | ✅ |
| | | test_alert_service.py | test_classify_priority_important_over_attention | 優先度ロジック | ✅ |
| | | test_alert_service.py | test_classify_unread | 未読検出 | ✅ |
| | | test_alert_service.py | test_classify_no_reaction | 未反応検出 | ✅ |
| | | test_alert_service.py | test_classify_not_submitted | 未提出検出 | ✅ |
| | | test_alert_service.py | test_classify_completed | 完了検出 | ✅ |

---

## 非機能要件のトレーサビリティ

| 要件 | テストファイル | テスト名 | カバレッジ | 状態 |
|-----|--------------|---------|----------|------|
| **パフォーマンス（N+1問題）** | test_n1_queries.py | test_diary_entry_str_without_n1_queries | N+1検証 | ✅ |
| | test_n1_queries.py | test_teacher_note_str_without_n1_queries | N+1検証 | ✅ |
| | test_n1_queries.py | test_daily_attendance_str_without_n1_queries | N+1検証 | ✅ |
| | test_n1_queries.py | test_teacher_note_read_status_str_without_n1_queries | N+1検証 | ✅ |
| | test_n1_queries.py | test_all_teachers_property_without_n1_queries | N+1検証 | ✅ |
| | test_alert_service.py | test_no_n_plus_one_problem | N+1検証 | ✅ |
| **データ整合性（バリデーション）** | test_model_validation.py | test_absent_with_reason_passes | バリデーション | ✅ |
| | test_model_validation.py | test_absent_without_reason_raises_error | バリデーション | ✅ |
| | test_model_validation.py | test_present_with_reason_raises_error | バリデーション | ✅ |
| | test_model_validation.py | test_present_without_reason_passes | バリデーション | ✅ |
| | test_model_validation.py | test_grade_leader_with_managed_grade_passes | バリデーション | ✅ |
| | test_model_validation.py | test_grade_leader_without_managed_grade_raises_error | バリデーション | ✅ |
| | test_model_validation.py | test_teacher_with_managed_grade_raises_error | バリデーション | ✅ |
| | test_model_validation.py | test_teacher_without_managed_grade_passes | バリデーション | ✅ |
| | test_model_validation.py | test_completed_with_all_fields_passes | バリデーション | ✅ |
| | test_model_validation.py | test_completed_without_completed_at_raises_error | バリデーション | ✅ |
| | test_model_validation.py | test_completed_without_completed_by_raises_error | バリデーション | ✅ |
| | test_model_validation.py | test_pending_without_completed_fields_passes | バリデーション | ✅ |
| **セキュリティ（権限チェック）** | test_classroom_admin.py | test_is_teacher_of_class_assistant_teacher | 権限チェック | ⚠️ 不足 |
| | test_classroom_admin.py | test_is_teacher_of_class_homeroom_teacher | 権限チェック | ⚠️ 不足 |
| | test_classroom_admin.py | test_is_teacher_of_class_other_teacher | 権限チェック | ⚠️ 不足 |
| | test_classroom_admin.py | test_assistant_teacher_can_view_diary_entries | 権限チェック | ⚠️ 不足 |
| | test_classroom_admin.py | test_homeroom_teacher_can_view_diary_entries | 権限チェック | ⚠️ 不足 |
| | test_ui.py | test_edit_delete_buttons_only_for_creator | 権限チェック | ⚠️ 不足 |
| **セキュリティ（CSRF）** | test_ui.py | test_csrf_token_exists | CSRF保護 | ✅ |
| **認証・ログインフロー** | test_admin_user_creation.py | test_student_login_redirect | ログインリダイレクト | ✅ |
| | test_admin_user_creation.py | test_teacher_login_redirect | ログインリダイレクト | ✅ |
| | test_admin_user_creation.py | test_grade_leader_login_redirect | ログインリダイレクト | ✅ |
| | test_admin_user_creation.py | test_school_leader_login_redirect | ログインリダイレクト | ✅ |
| | test_admin_user_creation.py | test_teacher_with_is_staff_login_redirect | is_staff対応 | ✅ |
| | test_admin_user_creation.py | test_grade_leader_with_is_staff_login_redirect | is_staff対応 | ✅ |
| | test_ui.py | test_root_url_redirects_to_login_when_unauthenticated | 未認証リダイレクト | ✅ |
| | test_ui.py | test_root_url_redirects_to_student_dashboard | 生徒リダイレクト | ✅ |
| | test_ui.py | test_logout_redirects_to_home_then_login | ログアウトフロー | ✅ |
| | test_ui.py | test_teacher_redirects_to_dashboard | 担任リダイレクト | ✅ |
| | test_ui.py | test_all_users_use_same_login_endpoint | allauth統合 | ✅ |
| | test_ui.py | test_admin_force_allauth_setting_enabled | allauth設定 | ✅ |

---

## Critical Gaps（要件カバー不足）

### 1. S-02: 連絡帳編集（既読前のみ） ❌

**要件**:
- 既読処理前のエントリーは編集可能
- 既読処理後のエントリーは編集不可

**現状**: テスト不足

**必要なテスト**:
```python
class TestDiaryEntryUpdateConstraints:
    def test_update_entry_before_read_success():
        # 既読前は編集可能

    def test_update_entry_after_read_forbidden():
        # 既読後は編集不可（403 Forbidden）

    def test_update_own_entry_only():
        # 他人のエントリーは編集不可
```

### 2. T-01, T-04, S-03: 閲覧機能の権限チェック ⚠️

**要件**:
- 担任は担当クラスの生徒のみ閲覧可能
- 生徒は自分の記録のみ閲覧可能

**現状**: UI表示のみテスト、権限チェックのテストなし

**必要なテスト**:
```python
class TestViewPermissions:
    def test_teacher_cannot_view_other_class_students():
        # 他クラスの生徒は閲覧不可（403 Forbidden）

    def test_student_cannot_view_other_students_entries():
        # 他の生徒のエントリーは閲覧不可（403 Forbidden）

    def test_teacher_can_view_assigned_class_only():
        # 割り当てられたクラスのみ閲覧可能
```

### 3. セキュリティテスト全般 ⚠️

**現状**: CSRF保護のみテスト

**必要なテスト**:
```python
class TestSecurity:
    def test_sql_injection_prevention():
        # SQLインジェクション対策

    def test_xss_prevention():
        # XSS対策

    def test_directory_traversal_prevention():
        # ディレクトリトラバーサル対策
```

---

## カバレッジサマリー

| カテゴリ | 総要件数 | カバー済み | 不足 | カバレッジ | 判定 |
|---------|---------|----------|------|----------|------|
| 必須機能（課題1） | 10 | 7 | 3 | 70% | ⚠️ |
| 改善機能（課題2） | 3 | 3 | 0 | 100% | ✅ |
| 非機能要件 | 4 | 3 | 1 | 75% | ⚠️ |
| **合計** | **17** | **13** | **4** | **76%** | **⚠️ 要改善** |

---

## 推奨アクション

### P0（即座）

1. **S-02テスト追加**（Critical Gap）
   - test_update_entry_before_read_success
   - test_update_entry_after_read_forbidden

2. **views.py権限チェックテスト追加**
   - test_teacher_cannot_view_other_class_students
   - test_student_cannot_view_other_students_entries

### P1（1-2週間）

3. **セキュリティテスト追加**
   - test_sql_injection_prevention
   - test_xss_prevention

4. **T-04, S-03の詳細テスト追加**
   - 検索・フィルタ機能のテスト
   - ページネーションのテスト

---

**作成日**: 2025-10-23
**作成者**: QA Lead
**次回更新**: views.pyテスト追加後

# 機能テストマッピング表

**作成日**: 2025-10-28
**対象**: v0.3.0-map
**目的**: 機能仕様とテストの対応関係を記録

---

## 凡例

- **F+U**: Feature Test + Unit Test
- **F**: Feature Test
- **U**: Unit Test
- **-**: テストなし

---

## システム共通

| ID | 画面 | URL | 状態 | テストファイル |
|----|------|-----|------|--------------|
| SYS-001 | ヘルスチェック | /health/ | F | test_system_features.py::TestSYS001HealthCheck (2件) |
| SYS-002 | ホームリダイレクト | / | F | test_auth_features.py::TestSYS002LoginRedirect (6件) |
| SYS-003 | About | /about/ | F | test_system_features.py::TestSYS003About (2件) |

---

## 認証

| ID | 画面 | URL | 状態 | テストファイル |
|----|------|-----|------|--------------|
| AUTH-001 | ログイン | /accounts/login/ | F | test_auth_features.py::TestAUTH001Login (2件) |
| AUTH-002 | ログアウト | /accounts/logout/ | F | test_auth_features.py::TestAUTH002Logout (1件) |
| AUTH-003 | パスワード変更 | /accounts/password/change/ | F | test_auth_features.py::TestAUTH003PasswordChange (3件) |
| AUTH-004 | パスワードリセット | /accounts/password/reset/ | F | test_auth_features.py::TestAUTH004To007PasswordReset (2件) |
| AUTH-005 | リセット完了 | /accounts/password/reset/done/ | F | test_auth_features.py::TestAUTH004To007PasswordReset (2件) |
| AUTH-006 | リセット確認 | /accounts/password/reset/key/<uidb64>/<token>/ | F | test_auth_features.py::TestAUTH004To007PasswordReset |
| AUTH-007 | リセット確認完了 | /accounts/password/reset/key/done/ | F | test_auth_features.py::TestAUTH004To007PasswordReset |

---

## 生徒

| ID | 画面 | URL | 状態 | テストファイル |
|----|------|-----|------|--------------|
| STU-001 | ダッシュボード | /diary/student/dashboard/ | F | test_student_features.py::TestSTU001StudentDashboard (1件) |
| STU-002 | 連絡帳作成 | /diary/create/ | F+U | F: test_student_features.py::TestSTU002DiaryCreation (3件)<br>U: test_services_logic.py::TestDiaryEntryServiceCreateEntry (4件)<br>U: test_forms_validation.py::TestDiaryEntryFormCleanEntryDate (2件) |
| STU-003 | 連絡帳編集 | /diary/diary/<int:pk>/edit/ | F+U | F: test_student_features.py::TestSTU003DiaryEditing (3件)<br>U: test_services_logic.py::TestDiaryEntryServiceUpdateEntry (2件)<br>U: test_models_logic.py::TestDiaryEntryIsEditable (2件) |
| STU-004 | 履歴 | /diary/history/ | F | test_student_features.py::TestSTU004DiaryHistory (1件) |

---

## 担任

| ID | 画面 | URL | 状態 | テストファイル |
|----|------|-----|------|--------------|
| TEA-001 | ダッシュボード | /diary/teacher/dashboard/ | F+U | F: test_teacher_features.py::TestTEA001TeacherDashboard (5件)<br>U: test_alert_service_logic.py (23件)<br>U: test_services_logic.py::TestTeacherDashboardService (6件) |
| TEA-002 | クラス健康 | /diary/teacher/class-health/ | F | test_teacher_features.py::TestTEA002ClassHealthDashboard (1件) |
| TEA-003 | 生徒詳細 | /diary/teacher/student/<int:student_id>/ | F | test_teacher_features.py::TestTEA003StudentDetail (2件) |

---

## 担任アクション

| ID | 機能 | URL | 状態 | テストファイル |
|----|------|-----|------|--------------|
| TEA-ACT-001 | 既読 | /diary/teacher/diary/<int:diary_id>/mark-as-read/ | F+U | F: test_teacher_actions.py::TestTEAACT001MarkAsRead (2件)<br>U: test_models_logic.py::TestDiaryEntryMarkAsRead (1件) |
| TEA-ACT-002 | 対応完了 | /diary/teacher/diary/<int:diary_id>/mark-action-completed/ | F+U | F: test_teacher_actions.py::TestTEAACT002MarkActionCompleted (1件)<br>U: test_models_logic.py::TestDiaryEntryMarkActionCompleted (2件) |
| TEA-ACT-003 | メモ追加 | /diary/teacher/note/add/<int:student_id>/ | F | test_teacher_actions.py::TestTEAACT003To005TeacherNotes (2件) |
| TEA-ACT-004 | メモ編集 | /diary/teacher/note/edit/<int:note_id>/ | F | test_teacher_actions.py::TestTEAACT003To005TeacherNotes (2件) |
| TEA-ACT-005 | メモ削除 | /diary/teacher/note/delete/<int:note_id>/ | F | test_teacher_actions.py::TestTEAACT003To005TeacherNotes (2件) |
| TEA-ACT-006 | 共有メモ既読 | /diary/teacher/note/<int:note_id>/mark-read/ | F | test_teacher_actions.py::TestTEAACT006MarkSharedNoteRead (1件) |
| TEA-ACT-007 | 出席保存 | /diary/teacher/attendance/save/ | F | test_teacher_actions.py::TestTEAACT007AttendanceSave (1件) |
| TEA-ACT-008 | 既読Quick | /diary/teacher/diary/<int:diary_id>/mark-as-read-quick/ | F | test_teacher_actions.py::TestTEAACT008MarkAsReadQuick (1件) |
| TEA-ACT-009 | タスク化 | /diary/teacher/diary/<int:diary_id>/create-task/ | F | test_teacher_actions.py::TestTEAACT009CreateTask (1件) |

---

## 管理職

| ID | 画面 | URL | 状態 | テストファイル |
|----|------|-----|------|--------------|
| GRD-001 | 学年統計 | /diary/grade-overview/ | F | test_grade_school_leader_features.py::TestGRD001GradeOverview (2件) |
| SCH-001 | 学校統計 | /diary/school-overview/ | F | test_grade_school_leader_features.py::TestSCH001SchoolOverview (2件) |
| ADM-001 | 管理画面 | /admin/ | F | test_grade_school_leader_features.py::TestADM001AdminAccess (2件) |

---

## ビジネスロジック

### alert_service.py

| 関数 | テスト | ファイル |
|------|--------|---------|
| classify_students() | 6件 | test_alert_service_logic.py::TestClassifyStudents* |
| _check_consecutive_decline() | 3件 | test_alert_service_logic.py::TestCheckConsecutiveDecline |
| _is_critical() | 2件 | test_alert_service_logic.py::TestIsCritical |
| _needs_action() | 3件 | test_alert_service_logic.py::TestNeedsAction |
| format_inline_history() | 2件 | test_alert_service_logic.py::TestFormatInlineHistory |
| get_snippet() | 3件 | test_alert_service_logic.py::TestGetSnippet |

### services/diary_entry_service.py

| メソッド | テスト | ファイル |
|---------|--------|---------|
| DiaryEntryService.create_entry() | 4件 | test_services_logic.py::TestDiaryEntryServiceCreateEntry |
| DiaryEntryService.update_entry() | 2件 | test_services_logic.py::TestDiaryEntryServiceUpdateEntry |

### services/teacher_dashboard_service.py

| メソッド | テスト | ファイル |
|---------|--------|---------|
| get_classroom_summary() | Feature | test_teacher_features.py |
| get_student_list_with_unread_count() | Feature | test_teacher_features.py |
| get_absence_data() | 2件 | test_services_logic.py::TestTeacherDashboardServiceGetAbsenceData |
| get_attendance_data_for_modal() | Feature | test_teacher_actions.py::TestTEAACT007 |
| get_shared_notes() | 4件 | test_services_logic.py::TestTeacherDashboardServiceGetSharedNotes |

---

## モデル

### DiaryEntry

| メソッド | テスト | ファイル |
|---------|--------|---------|
| clean() | 3件 | test_models_logic.py::TestDiaryEntryClean |
| mark_as_read() | 1件 | test_models_logic.py::TestDiaryEntryMarkAsRead |
| mark_action_completed() | 2件 | test_models_logic.py::TestDiaryEntryMarkActionCompleted |
| is_editable | 2件 | test_models_logic.py::TestDiaryEntryIsEditable |

### ClassRoom

| メソッド | テスト | ファイル |
|---------|--------|---------|
| student_count | 2件 | test_models_logic.py::TestClassRoomStudentCount |
| is_teacher_of_class() | 3件 | test_models_logic.py::TestClassRoomIsTeacherOfClass |

### UserProfile

| メソッド | テスト | ファイル |
|---------|--------|---------|
| clean() | 4件 | test_models_logic.py::TestUserProfileClean |

### その他

| モデル | テスト | ファイル |
|--------|--------|---------|
| TeacherNote | Feature | test_teacher_actions.py::TestTEAACT003To005 (6件) |
| TeacherNoteReadStatus | Feature | test_teacher_actions.py::TestTEAACT006 (1件) |
| DailyAttendance | Feature | test_teacher_actions.py::TestTEAACT007 (1件) |

---

## フォーム

### DiaryEntryForm

| メソッド | テスト | ファイル |
|---------|--------|---------|
| clean_entry_date() | 2件 | test_forms_validation.py::TestDiaryEntryFormCleanEntryDate |

### UserProfileAdminForm

| メソッド | テスト | ファイル |
|---------|--------|---------|
| clean() | 3件 | test_forms_validation.py::TestUserProfileAdminFormClean |

### CustomUserCreationForm

| メソッド | テスト | ファイル |
|---------|--------|---------|
| save() | 5件 | test_forms_validation.py::TestCustomUserCreationFormSave |
| clean_email() | 2件 | test_forms_validation.py::TestCustomUserCreationFormCleanEmail |
| clean() | 2件 | test_forms_validation.py::TestCustomUserCreationFormClean |

---

## シグナル・アダプター

### signals.py

| シグナル | テスト | ファイル |
|---------|--------|---------|
| create_user_profile | 4件 | test_signals.py::TestCreateUserProfileSignal |

### adapters.py

| メソッド | テスト | ファイル |
|---------|--------|---------|
| get_login_redirect_url() | Feature | test_auth_features.py::TestSYS002LoginRedirect (6件) |
| clean_email() | 3件 | test_adapters.py::TestRoleBasedRedirectAdapterCleanEmail |
| is_open_for_signup() | 1件 | test_adapters.py::TestRoleBasedRedirectAdapterIsOpenForSignup |

---

## 統計

| カテゴリ | 機能数 | Feature | Unit | カバレッジ |
|---------|-------|---------|------|-----------|
| システム共通 | 3 | 3 | 0 | 100% |
| 認証 | 7 | 7 | 0 | 100% |
| 生徒 | 4 | 4 | 8 | 100% |
| 担任 | 3 | 3 | 29 | 100% |
| 担任アクション | 9 | 9 | 3 | 100% |
| 管理職 | 3 | 3 | 0 | 100% |
| サービスクラス | 11 | 3 | 26 | 100% |
| モデル | 7 | 3 | 17 | 100% |
| フォーム | 5 | 0 | 13 | 100% |
| シグナル・アダプター | 4 | 1 | 8 | 100% |
| **合計** | **56** | **36** | **104** | **100%** |

---

## テストファイル一覧

### Feature Tests (6ファイル、53件)
- test_auth_features.py (14件)
- test_student_features.py (7件)
- test_teacher_features.py (5件)
- test_teacher_actions.py (13件)
- test_grade_school_leader_features.py (5件)
- test_system_features.py (4件)

### Unit Tests (6ファイル、70件)
- test_models_logic.py (16件)
- test_forms_validation.py (13件)
- test_alert_service_logic.py (23件)
- test_services_logic.py (12件)
- test_signals.py (4件)
- test_adapters.py (2件)

---

## テスト実行

全テスト:
```bash
docker compose -f docker-compose.local.yml exec django pytest school_diary/diary/tests/ -v
```

Unit Testsのみ:
```bash
docker compose -f docker-compose.local.yml exec django pytest school_diary/diary/tests/unit/ -v
```

Feature Testsのみ:
```bash
docker compose -f docker-compose.local.yml exec django pytest school_diary/diary/tests/features/ -v
```

---

**最終更新**: 2025-10-28

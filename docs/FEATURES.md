# 機能一覧

---

## 画面一覧

### システム共通

| ID      | 画面名             | URL      | アクセス権 | 主要機能                                           | 実装場所                     |
| ------- | ------------------ | -------- | ---------- | -------------------------------------------------- | ---------------------------- |
| SYS-001 | ヘルスチェック     | /health/ | 全ユーザー | 死活監視、ステータス確認                           | config/urls.py::health_check |
| SYS-002 | ホームリダイレクト | /        | 全ユーザー | 未認証 → ログイン、認証済み → 役割別ダッシュボード | views/auth.py::home_redirect_view |
| SYS-003 | About              | /about/  | 全ユーザー | システム概要                                       | TemplateView                 |

### 認証関連（django-allauth）

| ID       | 画面名                     | URL                                                        | アクセス権     | 主要機能                         | 実装場所                       |
| -------- | -------------------------- | ---------------------------------------------------------- | -------------- | -------------------------------- | ------------------------------ |
| AUTH-001 | ログイン                   | /accounts/login/                                           | 未認証ユーザー | ログイン処理                     | django-allauth                 |
| AUTH-002 | ログアウト                 | /accounts/logout/                                          | 認証ユーザー   | ログアウト処理                   | django-allauth                 |
| AUTH-003 | パスワード変更             | /accounts/password/change/                                 | 認証ユーザー   | パスワード変更（初回ログイン時） | views/auth.py::password_change_view |
| AUTH-004 | パスワードリセット         | /accounts/password/reset/                                  | 全ユーザー     | パスワードリセット要求           | django-allauth                 |
| AUTH-005 | パスワードリセット完了     | /accounts/password/reset/done/                             | 全ユーザー     | リセットメール送信完了           | django-allauth                 |
| AUTH-006 | パスワードリセット確認     | /accounts/password/reset/key/&lt;uidb64&gt;/&lt;token&gt;/ | 全ユーザー     | 新パスワード入力                 | django-allauth                 |
| AUTH-007 | パスワードリセット確認完了 | /accounts/password/reset/key/done/                         | 全ユーザー     | パスワード変更完了               | django-allauth                 |

### 生徒用画面

| ID      | 画面名             | URL                               | アクセス権               | 主要機能                              | 実装場所                       |
| ------- | ------------------ | --------------------------------- | ------------------------ | ------------------------------------- | ------------------------------ |
| STU-001 | 生徒ダッシュボード | /diary/student/dashboard/         | 生徒                     | 過去 7 日分の連絡帳表示、提出状況確認 | views/student.py::StudentDashboardView |
| STU-002 | 連絡帳作成         | /diary/create/                    | 生徒                     | 連絡帳新規作成、一日一件制約チェック  | views/student.py::DiaryCreateView      |
| STU-003 | 連絡帳編集         | /diary/diary/&lt;int:pk&gt;/edit/ | 生徒（本人、既読前のみ） | 連絡帳編集（既読後は編集不可）        | views/student.py::DiaryUpdateView      |
| STU-004 | 連絡帳履歴         | /diary/history/                   | 生徒                     | 過去の連絡帳一覧、ページネーション    | views/student.py::DiaryHistoryView     |

### 担任用画面

| ID      | 画面名                   | URL                                            | アクセス権             | 主要機能                                                                                                             | 実装場所                           |
| ------- | ------------------------ | ---------------------------------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| TEA-001 | 担任ダッシュボード       | /diary/teacher/dashboard/                      | 担任                   | Inbox Pattern（6 カテゴリ分類）、アラート表示、出席記録、要対応タスク管理、未提出セクション折りたたみ、タスク化 AJAX | views/teacher.py::TeacherDashboardView     |
| TEA-002 | クラス健康ダッシュボード | /diary/teacher/class-health/                   | 担任                   | クラス健康状態ヒートマップ（7 日/14 日）                                                                             | views/management.py::ClassHealthDashboardView |
| TEA-003 | 生徒詳細                 | /diary/teacher/student/&lt;int:student_id&gt;/ | 担任（担当クラスのみ） | 個別生徒の連絡帳履歴、担任メモ表示                                                                                   | views/teacher.py::TeacherStudentDetailView |

### 担任用アクション（POST）

| ID          | 機能名                  | URL                                                              | アクセス権             | 主要機能                                                              | 実装場所                                |
| ----------- | ----------------------- | ---------------------------------------------------------------- | ---------------------- | --------------------------------------------------------------------- | --------------------------------------- |
| TEA-ACT-001 | 既読処理                | /diary/teacher/diary/&lt;int:diary_id&gt;/mark-as-read/          | 担任（担当クラスのみ） | 既読処理、反応・対応記録の更新                                        | views/teacher.py::teacher_mark_as_read          |
| TEA-ACT-002 | 対応完了処理            | /diary/teacher/diary/&lt;int:diary_id&gt;/mark-action-completed/ | 担任（担当クラスのみ） | 対応完了処理                                                          | views/teacher.py::teacher_mark_action_completed |
| TEA-ACT-003 | メモ追加                | /diary/teacher/note/add/&lt;int:student_id&gt;/                  | 担任（担当クラスのみ） | 担任メモ追加（個人メモ・学年共有メモ）                                | views/teacher.py::teacher_add_note              |
| TEA-ACT-004 | メモ編集                | /diary/teacher/note/edit/&lt;int:note_id&gt;/                    | 担任（作成者のみ）     | 担任メモ編集                                                          | views/teacher.py::teacher_edit_note             |
| TEA-ACT-005 | メモ削除                | /diary/teacher/note/delete/&lt;int:note_id&gt;/                  | 担任（作成者のみ）     | 担任メモ削除                                                          | views/teacher.py::teacher_delete_note           |
| TEA-ACT-006 | 共有メモ既読            | /diary/teacher/note/&lt;int:note_id&gt;/mark-read/               | 担任（共有メモのみ）   | 学年共有メモ既読処理                                                  | views/teacher.py::mark_shared_note_read         |
| TEA-ACT-007 | 出席保存                | /diary/teacher/attendance/save/                                  | 担任（担当クラスのみ） | 出席記録保存                                                          | views/teacher.py::teacher_save_attendance       |
| TEA-ACT-008 | 既読処理（Quick、AJAX） | /diary/teacher/diary/&lt;int:diary_id&gt;/mark-as-read-quick/    | 担任（担当クラスのみ） | 既読処理のみ（AJAX）、action_status=NOT_REQUIRED 設定                 | views/teacher.py::teacher_mark_as_read_quick    |
| TEA-ACT-009 | タスク化（AJAX）        | /diary/teacher/diary/&lt;int:diary_id&gt;/create-task/           | 担任（担当クラスのみ） | タスク化（AJAX）、既読+internal_action 設定+action_status=IN_PROGRESS | views/teacher.py::teacher_create_task_from_card |

### 学年主任用画面

| ID      | 画面名   | URL                    | アクセス権 | 主要機能                           | 実装場所                    |
| ------- | -------- | ---------------------- | ---------- | ---------------------------------- | --------------------------- |
| GRD-001 | 学年統計 | /diary/grade-overview/ | 学年主任   | 学年統計、クラス比較、メンタル推移 | views/management.py::GradeOverviewView |

### 校長/教頭用画面

| ID      | 画面名   | URL                     | アクセス権 | 主要機能                       | 実装場所                     |
| ------- | -------- | ----------------------- | ---------- | ------------------------------ | ---------------------------- |
| SCH-001 | 学校統計 | /diary/school-overview/ | 校長/教頭  | 学校全体統計、学級閉鎖判断支援 | views/management.py::SchoolOverviewView |

### システム管理者用

| ID      | 画面名          | URL     | アクセス権     | 主要機能                                                 | 実装場所     |
| ------- | --------------- | ------- | -------------- | -------------------------------------------------------- | ------------ |
| ADM-001 | Django 管理画面 | /admin/ | システム管理者 | ユーザー・クラス管理、役割ベースアクセス制御、データ管理 | Django admin |

---

補足:

- `TEA-002` のクラス健康ダッシュボードは、担任向け機能ですが統計系画面として `views/management.py` に実装されています。
- 詳細な業務ロジックや内部 service 構成は [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md) を参照してください。

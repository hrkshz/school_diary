# 機能一覧

> **対象**: 連絡帳管理システム（school_diary）
> **バージョン**: v0.3.0-map
> **作成日**: 2025-10-22

---

## 画面一覧

### システム共通

| ID | 画面名 | URL | アクセス権 | 主要機能 | 実装場所 |
|----|--------|-----|-----------|---------|---------|
| SYS-001 | ヘルスチェック | /health/ | 全ユーザー | 死活監視、ステータス確認 | config/urls.py::health_check |
| SYS-002 | ホームリダイレクト | / | 全ユーザー | 未認証 → ログイン、認証済み → 役割別ダッシュボード | views.py::home_redirect_view |
| SYS-003 | About | /about/ | 全ユーザー | システム概要 | TemplateView |

### 認証関連（django-allauth）

| ID | 画面名 | URL | アクセス権 | 主要機能 | 実装場所 |
|----|--------|-----|-----------|---------|---------|
| AUTH-001 | ログイン | /accounts/login/ | 未認証ユーザー | ログイン処理 | django-allauth |
| AUTH-002 | ログアウト | /accounts/logout/ | 認証ユーザー | ログアウト処理 | django-allauth |
| AUTH-003 | パスワード変更 | /accounts/password/change/ | 認証ユーザー | パスワード変更（初回ログイン時） | views.py::password_change_view |
| AUTH-004 | パスワードリセット | /accounts/password/reset/ | 全ユーザー | パスワードリセット要求 | django-allauth |
| AUTH-005 | パスワードリセット完了 | /accounts/password/reset/done/ | 全ユーザー | リセットメール送信完了 | django-allauth |
| AUTH-006 | パスワードリセット確認 | /accounts/password/reset/key/&lt;uidb64&gt;/&lt;token&gt;/ | 全ユーザー | 新パスワード入力 | django-allauth |
| AUTH-007 | パスワードリセット確認完了 | /accounts/password/reset/key/done/ | 全ユーザー | パスワード変更完了 | django-allauth |

### 生徒用画面

| ID | 画面名 | URL | アクセス権 | 主要機能 | 実装場所 |
|----|--------|-----|-----------|---------|---------|
| STU-001 | 生徒ダッシュボード | /diary/student/dashboard/ | 生徒 | 過去7日分の連絡帳表示、提出状況確認 | views.py::StudentDashboardView |
| STU-002 | 連絡帳作成 | /diary/create/ | 生徒 | 連絡帳新規作成、一日一件制約チェック | views.py::DiaryCreateView |
| STU-003 | 連絡帳編集 | /diary/diary/&lt;int:pk&gt;/edit/ | 生徒（本人、既読前のみ） | 連絡帳編集（既読後は編集不可） | views.py::DiaryUpdateView |
| STU-004 | 連絡帳履歴 | /diary/history/ | 生徒 | 過去の連絡帳一覧、ページネーション | views.py::DiaryHistoryView |

### 担任用画面

| ID | 画面名 | URL | アクセス権 | 主要機能 | 実装場所 |
|----|--------|-----|-----------|---------|---------|
| TEA-001 | 担任ダッシュボード | /diary/teacher/dashboard/ | 担任 | Inbox Pattern（6カテゴリ分類）、アラート表示、出席記録、要対応タスク管理、未提出セクション折りたたみ、タスク化AJAX | views.py::TeacherDashboardView |
| TEA-002 | クラス健康ダッシュボード | /diary/teacher/class-health/ | 担任 | クラス健康状態ヒートマップ（7日/14日） | views.py::ClassHealthDashboardView |
| TEA-003 | 生徒詳細 | /diary/teacher/student/&lt;int:student_id&gt;/ | 担任（担当クラスのみ） | 個別生徒の連絡帳履歴、担任メモ表示 | views.py::TeacherStudentDetailView |

### 担任用アクション（POST）

| ID | 機能名 | URL | アクセス権 | 主要機能 | 実装場所 |
|----|--------|-----|-----------|---------|---------|
| TEA-ACT-001 | 既読処理 | /diary/teacher/diary/&lt;int:diary_id&gt;/mark-as-read/ | 担任（担当クラスのみ） | 既読処理、反応・対応記録の更新 | views.py::teacher_mark_as_read |
| TEA-ACT-002 | 対応完了処理 | /diary/teacher/diary/&lt;int:diary_id&gt;/mark-action-completed/ | 担任（担当クラスのみ） | 対応完了処理 | views.py::teacher_mark_action_completed |
| TEA-ACT-003 | メモ追加 | /diary/teacher/note/add/&lt;int:student_id&gt;/ | 担任（担当クラスのみ） | 担任メモ追加（個人メモ・学年共有メモ） | views.py::teacher_add_note |
| TEA-ACT-004 | メモ編集 | /diary/teacher/note/edit/&lt;int:note_id&gt;/ | 担任（作成者のみ） | 担任メモ編集 | views.py::teacher_edit_note |
| TEA-ACT-005 | メモ削除 | /diary/teacher/note/delete/&lt;int:note_id&gt;/ | 担任（作成者のみ） | 担任メモ削除 | views.py::teacher_delete_note |
| TEA-ACT-006 | 共有メモ既読 | /diary/teacher/note/&lt;int:note_id&gt;/mark-read/ | 担任（共有メモのみ） | 学年共有メモ既読処理 | views.py::mark_shared_note_read |
| TEA-ACT-007 | 出席保存 | /diary/teacher/attendance/save/ | 担任（担当クラスのみ） | 出席記録保存 | views.py::teacher_save_attendance |
| TEA-ACT-008 | 既読処理（Quick、AJAX） | /diary/teacher/diary/&lt;int:diary_id&gt;/mark-as-read-quick/ | 担任（担当クラスのみ） | 既読処理のみ（AJAX）、action_status=NOT_REQUIRED設定 | views.py::teacher_mark_as_read_quick |
| TEA-ACT-009 | タスク化（AJAX） | /diary/teacher/diary/&lt;int:diary_id&gt;/create-task/ | 担任（担当クラスのみ） | タスク化（AJAX）、既読+internal_action設定+action_status=IN_PROGRESS | views.py::teacher_create_task_from_card |

### 学年主任用画面

| ID | 画面名 | URL | アクセス権 | 主要機能 | 実装場所 |
|----|--------|-----|-----------|---------|---------|
| GRD-001 | 学年統計 | /diary/grade-overview/ | 学年主任 | 学年統計、クラス比較、メンタル推移 | views.py::GradeOverviewView |

### 校長/教頭用画面

| ID | 画面名 | URL | アクセス権 | 主要機能 | 実装場所 |
|----|--------|-----|-----------|---------|---------|
| SCH-001 | 学校統計 | /diary/school-overview/ | 校長/教頭 | 学校全体統計、学級閉鎖判断支援 | views.py::SchoolOverviewView |

### システム管理者用

| ID | 画面名 | URL | アクセス権 | 主要機能 | 実装場所 |
|----|--------|-----|-----------|---------|---------|
| ADM-001 | Django管理画面 | /admin/ | システム管理者 | ユーザー・クラス管理、役割ベースアクセス制御、データ管理 | Django admin |

---

## 補足: ログインリダイレクトロジック

### adapters.py::RoleBasedRedirectAdapter
ログイン後のリダイレクト先を役割に応じて決定

| 優先順位 | 条件 | リダイレクト先 |
|---------|------|--------------|
| 1 | is_superuser=True | /admin/（Django管理画面） |
| 2 | role='school_leader' | /diary/school-overview/（学校統計） |
| 3 | role='grade_leader' | /diary/grade-overview/（学年統計） |
| 4 | role='teacher' または homeroom_teacher | /diary/teacher/dashboard/（担任ダッシュボード） |
| 5 | 上記以外（生徒） | /diary/student/dashboard/（生徒ダッシュボード） |

---

## 主要サービスクラス

### alert_service.py
Inbox Pattern実装、早期警告システム、要対応タスク管理

| 関数名 | 責務 |
|--------|------|
| classify_students() | 生徒を6カテゴリに分類（P0重要、P1要注意、P1.5要対応タスク、P2-1未提出、P2-2未読、P3完了済み） |
| _check_consecutive_decline() | 3日連続メンタル低下検知 |
| _is_critical() | メンタル★1検知（即時対応） |
| _needs_action() | internal_action設定済みかつaction_status=PENDING/IN_PROGRESS検知 |
| format_inline_history() | 3日間履歴フォーマット |
| get_snippet() | 連絡帳本文スニペット生成 |

**UI改善（2025-10-24）**:
- P1.5（要対応タスク）: 既読ボタン削除、詳細リンクのみ表示
- P2-1（未提出）: disabledボタン削除、Bootstrap Collapseで折りたたみ可能（デフォルト折りたたみ）
- タスク化モーダル: internal_action選択肢を日本語化（models.InternalActionと統一）

### services/diary_entry_service.py
連絡帳エントリーのビジネスロジック

| クラス名 | メソッド | 責務 |
|---------|---------|------|
| DiaryEntryService | create_entry() | 連絡帳エントリー新規作成、classroom自動設定 |
| DiaryEntryService | update_entry() | 連絡帳エントリー更新、action_status管理 |

### services/teacher_dashboard_service.py
担任ダッシュボードのビジネスロジック

| クラス名 | メソッド | 責務 |
|---------|---------|------|
| TeacherDashboardService | get_classroom_summary() | サマリー統計計算（未読数、対応待ち数、緊急対応数） |
| TeacherDashboardService | get_student_list_with_unread_count() | 生徒一覧取得（未読件数アノテーション、N+1最適化） |
| TeacherDashboardService | get_absence_data() | 本日の欠席者情報集計（欠席理由別集計） |
| TeacherDashboardService | get_attendance_data_for_modal() | 出席モーダル用データ取得（既存データ読み込み） |
| TeacherDashboardService | get_shared_notes() | 学年共有メモ取得（14日以内、他担任作成、未読のみ） |

---

## 主要モデル

### models.py

| モデル名 | 責務 |
|---------|------|
| DiaryEntry | 連絡帳エントリー（体調、メンタル、振り返り、反応・対応記録） |
| ClassRoom | クラス情報（学年、組、年度、担任、生徒） |
| UserProfile | ユーザープロフィール（5ロール: 生徒、担任、学年主任、校長/教頭、システム管理者） |
| TeacherNote | 担任メモ（個人メモ・学年共有メモ） |
| TeacherNoteReadStatus | 担任メモ既読状態管理 |
| DailyAttendance | 出席記録（出席、欠席、遅刻、早退） |

---

## アクセス権限マトリクス

| 機能 | 生徒 | 担任 | 学年主任 | 校長/教頭 | システム管理者 |
|-----|-----|-----|---------|----------|--------------|
| 連絡帳作成・編集 | ○（本人のみ、既読前） | - | - | - | ○ |
| 連絡帳閲覧 | ○（本人のみ） | ○（担当クラスのみ） | ○（担当学年） | ○（全校） | ○ |
| 既読処理 | - | ○（担当クラスのみ） | - | - | ○ |
| 担任メモ | - | ○（作成・編集・削除） | ○（共有メモ閲覧・既読） | - | ○ |
| 出席記録 | - | ○（担当クラスのみ） | - | - | ○ |
| 学年統計 | - | - | ○（担当学年のみ） | - | ○ |
| 学校統計 | - | - | - | ○ | ○ |
| ユーザー管理 | - | - | - | - | ○ |

---

## API仕様（AJAX）

### JSONレスポンス形式

全てのAJAX APIは統一された形式でレスポンスを返す。

#### 成功時

```json
{
  "status": "success",
  "message": "処理が完了しました"
}
```

#### 失敗時

```json
{
  "status": "error",
  "message": "エラーの理由"
}
```

### リクエストデータ形式

AJAX APIは2つの形式でデータを受け取る：

#### Form-encoded形式（大部分のAPI）

`application/x-www-form-urlencoded` 形式（POST data）

```javascript
// 例: teacher_save_attendance
fetch('/diary/teacher/attendance/save/', {
  method: 'POST',
  headers: {
    'X-CSRFToken': csrfToken,
    'X-Requested-With': 'XMLHttpRequest'
  },
  body: new URLSearchParams({
    'student_id': '123',
    'date': '2025-10-24',
    'status': 'present'
  })
})
```

#### JSON形式（一部のAPI）

`application/json` 形式（TEA-ACT-009: teacher_create_task_from_cardのみ）

```javascript
// 例: teacher_create_task_from_card
fetch('/diary/teacher/diary/456/create-task/', {
  method: 'POST',
  headers: {
    'X-CSRFToken': csrfToken,
    'X-Requested-With': 'XMLHttpRequest',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    'internal_action': 'parent_contact'
  })
})
```

### AJAX検出

サーバー側は `X-Requested-With: XMLHttpRequest` ヘッダーでAJAXリクエストを判定する。

```python
if request.headers.get("X-Requested-With") == "XMLHttpRequest":
    return JsonResponse({"status": "success", "message": "..."})
```

---

## セキュリティポリシー

### HTTPステータスコード使い分け

| ケース | HTTPステータス | 理由 |
|--------|---------------|------|
| リソースが存在しない | 404 Not Found | 正常な挙動 |
| **他クラスの連絡帳にアクセス** | **403 Forbidden** | **IDの存在を隠蔽（セキュリティ）** |
| **他担任のメモにアクセス** | **403 Forbidden** | **IDの存在を隠蔽（セキュリティ）** |
| 担任権限なし | 403 Forbidden | 権限不足 |
| メソッド不正 | 405 Method Not Allowed | POST以外のリクエスト |
| バリデーションエラー | 400 Bad Request | データ不正 |

### 権限チェックの順序

セキュリティ上、以下の順序で権限チェックを実施する：

```python
# ステップ1: リソースを取得（IDの存在確認）
diary = get_object_or_404(DiaryEntry, id=diary_id)

# ステップ2: 権限チェック（クラス所属確認）
if diary.student not in classroom.students.all():
    return HttpResponseForbidden("このクラスの生徒の連絡帳ではありません。")
```

**理由**: `get_object_or_404(DiaryEntry, id=diary_id, student__classes=classroom)` のように一度に取得すると、他クラスの連絡帳に対して404を返してしまい、IDの存在が推測可能になる。

### 情報漏洩防止

エラーメッセージは以下の原則に従う：

| ケース | ❌ 悪い例 | ✅ 良い例 |
|--------|----------|----------|
| 他クラスの連絡帳 | "連絡帳が見つかりません"（404） | "このクラスの生徒の連絡帳ではありません"（403） |
| 他担任のメモ | "メモが見つかりません"（404） | "このメモを編集する権限がありません"（403） |
| 存在しないID | "権限がありません"（403） | "連絡帳が見つかりません"（404） |

---

## 開発者向け詳細仕様

より詳細な技術仕様（AJAX API詳細仕様、リクエスト/レスポンス例等）は以下を参照してください：
- [docs/03-features.md](../docs/03-features.md) - 完全版（開発者・保守担当者向け）

---

**最終更新**: 2025-10-29（評価者向けに最適化）

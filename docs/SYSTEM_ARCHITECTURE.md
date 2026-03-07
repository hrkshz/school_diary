# 連絡帳管理システム - アプリケーション構成解説

> **対象読者**: システム理解、面談説明、保守引き継ぎ

本書は、現在の Django アプリケーション構成と責務分担を理解するためのドキュメントです。

---

## 1. 全体像

```text
Template
  ↓
View
  ↓
Service / Authorization / Utility
  ↓
Model
  ↓
Database
```

設計方針:

- View は薄く保つ
- 業務ロジックは `services/` に集約する
- 認可は `authorization.py` に集約する
- 年度や共通値は `academic_year.py` / `constants.py` に寄せる

---

## 2. 現在のディレクトリ構成

```text
school_diary/diary/
├── academic_year.py                  # 学校年度の算出
├── authorization.py                 # ロールとアクセス判定
├── constants.py                     # 共通定数
├── models.py                        # DB モデル定義
├── forms.py                         # 入力フォーム定義
├── admin.py                         # Django Admin 設定
├── adapters.py                      # 外部ライブラリ連携の調整
├── middleware.py                    # リクエスト共通処理
├── signals.py                       # モデル保存時の補助処理
├── utils.py                         # 共通ユーティリティ
├── urls.py                          # diary アプリの URL 定義
├── views/
│   ├── auth.py                      # ホーム遷移、パスワード変更、health check
│   ├── student.py                   # 生徒向け画面
│   ├── teacher.py                   # 担任向け画面と担任操作
│   ├── management.py                # 学年主任・校長向け統計画面
│   └── admin_views.py               # テストデータ作成画面
└── services/
    ├── alert_service.py             # Inbox Pattern の分類
    ├── diary_entry_service.py       # 既読・対応・出席の状態更新
    ├── teacher_note_service.py      # 担任メモの作成・更新・既読
    ├── teacher_dashboard_service.py # 担任ダッシュボード集計
    └── management_dashboard_service.py # 学年/学校ダッシュボード集計
```

以下では主要な責務を先に一覧し、詳細は次章で補足します。

---

## 3. 役割ごとの責務

### `models.py`

- DB テーブル定義
- 最低限のバリデーション
- QuerySet / Manager

主要モデル:

- `DiaryEntry`
- `ClassRoom`
- `UserProfile`
- `TeacherNote`
- `TeacherNoteReadStatus`
- `DailyAttendance`

### `views/`

- HTTP リクエスト受付
- 権限確認
- service 呼び出し
- テンプレート返却 / JSON 返却

構成:

- `auth.py`: ホームリダイレクト、パスワード変更、health check
- `student.py`: 生徒画面
- `teacher.py`: 担任画面、AJAX 操作、メモ、出席
- `management.py`: 学年主任 / 校長の統計画面
- `admin_views.py`: テストデータ作成画面

### `services/`

- `diary_entry_service.py`: 既読、タスク化、完了、出席保存
- `teacher_note_service.py`: メモ作成・更新・削除・既読
- `teacher_dashboard_service.py`: 担任ダッシュボード用集計
- `management_dashboard_service.py`: 学年/学校統計集計
- `alert_service.py`: Inbox Pattern 分類

### `authorization.py`

役割:

- 役割判定
- アクセス可能クラス / 生徒の判定
- 主担任/副担任のアクセス整理

主な関数:

- `get_primary_classroom(user)`
- `get_accessible_students(user)`
- `can_access_student(user, student)`
- `can_access_classroom(user, classroom)`

### `academic_year.py`

- 日本の学校年度（4 月始まり）の算出
- 年度固定値の散在防止

---

## 4. URL と画面

主要 URL:

- `/diary/student/dashboard/`
- `/diary/create/`
- `/diary/history/`
- `/diary/teacher/dashboard/`
- `/diary/teacher/class-health/`
- `/diary/grade-overview/`
- `/diary/school-overview/`
- `/admin/`

URL ルーティング:

```text
config/urls.py
  └── /diary/ → school_diary.diary.urls

school_diary/diary/urls.py
  └── 各 view module を明示 import
```

---

## 5. 代表的な処理フロー

### 生徒が連絡帳を提出する流れ

```text
DiaryCreateView
  → DiaryEntryForm
  → DiaryEntryService.create_entry()
  → DiaryEntry 保存
  → student dashboard へリダイレクト
```

### 担任が既読にする流れ

```text
teacher_mark_as_read()
  → authorization で対象確認
  → DiaryEntryService.mark_read()
  → student detail へリダイレクト
```

### ダッシュボード表示

```text
TeacherDashboardView
  → TeacherDashboardService.get_dashboard_data(user)
  → alert_service / 集計 / 履歴整形
  → template context に展開
```

---

## 6. この構成のメリット

- どこを見ればよいかが分かりやすい
- View と業務ロジックが分かれている
- 認可と年度処理が横断的に再利用できる
- ダッシュボード集計の変更が画面コードに波及しにくい

---

## 7. 関連ドキュメント

- [TECHNICAL_SPECIFICATION.md](./TECHNICAL_SPECIFICATION.md)
- [SYSTEM_FLOW_GUIDE.md](./SYSTEM_FLOW_GUIDE.md)
- [ER_DIAGRAM.md](./ER_DIAGRAM.md)

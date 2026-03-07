# システム処理フローガイド

> **対象読者**: 実装の場所と処理の流れを短時間で把握したい人
> **目的**: 「どこで受けて、どこで判定し、どこで保存するか」を追いやすくする

---

## 1. 全体像

```text
Browser
  -> config/urls.py
  -> school_diary/diary/urls.py
  -> views/{auth,student,teacher,management,admin_views}.py
  -> services/* or authorization.py
  -> models.py
  -> PostgreSQL
  -> Template / Redirect / JSON response
```

現在は `views.py` 1 枚構成ではなく、画面種別ごとに `views/` 配下へ分割しています。

---

## 2. 主なファイル配置

```text
school_diary/diary/
├── models.py
├── forms.py
├── urls.py
├── academic_year.py
├── authorization.py
├── adapters.py
├── views/
│   ├── auth.py
│   ├── student.py
│   ├── teacher.py
│   ├── management.py
│   └── admin_views.py
└── services/
    ├── alert_service.py
    ├── diary_entry_service.py
    ├── teacher_note_service.py
    ├── teacher_dashboard_service.py
    └── management_dashboard_service.py
```

役割:

- `views/`: HTTP の入口。認証・認可・service 呼び出し・レスポンス返却
- `services/`: 業務ロジックと集計
- `authorization.py`: ロール判定とアクセス判定
- `academic_year.py`: 年度計算の正本
- `models.py`: データ構造と最低限の整合性

---

## 3. ログイン後の分岐

```text
Login success
  -> adapters.RoleBasedRedirectAdapter
  -> superuser        -> /admin/
  -> school_leader    -> /diary/school-overview/
  -> grade_leader     -> /diary/grade-overview/
  -> teacher/homeroom -> /diary/teacher/dashboard/
  -> student          -> /diary/student/dashboard/
```

関連ファイル:

- `school_diary/diary/adapters.py`
- `school_diary/diary/views/auth.py`

---

## 4. 代表的な処理フロー

### 生徒が連絡帳を作成する

```text
POST /diary/create/
  -> views/student.py::DiaryCreateView
  -> form validation
  -> DiaryEntryService.create_entry()
  -> DiaryEntry 保存
  -> /diary/student/dashboard/ へ redirect
```

見る場所:

- `school_diary/diary/views/student.py`
- `school_diary/diary/forms.py`
- `school_diary/diary/services/diary_entry_service.py`

### 担任が既読にする

```text
POST /diary/teacher/diary/<id>/mark-as-read/
  -> views/teacher.py::teacher_mark_as_read
  -> authorization.can_access_student(...)
  -> DiaryEntryService.mark_read(...)
  -> redirect
```

見る場所:

- `school_diary/diary/views/teacher.py`
- `school_diary/diary/authorization.py`
- `school_diary/diary/services/diary_entry_service.py`

### 担任がメモを共有する

```text
POST /diary/teacher/note/add/<student_id>/
  -> views/teacher.py::teacher_add_note
  -> TeacherNoteService.create_note(...)
  -> TeacherNote 保存
  -> redirect
```

見る場所:

- `school_diary/diary/views/teacher.py`
- `school_diary/diary/services/teacher_note_service.py`

### 担任ダッシュボードを表示する

```text
GET /diary/teacher/dashboard/
  -> views/teacher.py::TeacherDashboardView
  -> TeacherDashboardService.get_dashboard_data(user)
  -> alert_service で分類・整形
  -> template に context を渡す
```

見る場所:

- `school_diary/diary/views/teacher.py`
- `school_diary/diary/services/teacher_dashboard_service.py`
- `school_diary/diary/services/alert_service.py`

### 学年/学校ダッシュボードを表示する

```text
GET /diary/grade-overview/
GET /diary/school-overview/
  -> views/management.py
  -> ManagementDashboardService
  -> academic_year.py で対象年度決定
  -> template に context を渡す
```

見る場所:

- `school_diary/diary/views/management.py`
- `school_diary/diary/services/management_dashboard_service.py`
- `school_diary/diary/academic_year.py`

---

## 5. 認可の見方

アクセス制御を確認したいときは、まず `authorization.py` を見ます。

主な関数:

- `get_primary_classroom(user)`
- `get_accessible_students(user)`
- `can_access_student(user, student)`
- `can_access_classroom(user, classroom)`

方針:

- view 側で生徒やクラスへのアクセス可否を直接書き散らさない
- ロール文字列の直書きを避ける
- 不正アクセスは `PermissionDenied` で統一する

---

## 6. 年度の見方

年度の基準は `academic_year.py` にまとめています。

考え方:

- 4 月始まりの学校年度を使う
- `2025` のような固定値を view や service に散らさない
- 学年統計・学校統計はこの関数を基準に最新年度を決める

---

## 7. 困ったときの見方

- 「画面がどこで始まるか」: `config/urls.py` -> `school_diary/diary/urls.py`
- 「保存処理はどこか」: `views/*` から呼ばれる `services/*`
- 「見える/見えないの判定はどこか」: `authorization.py`
- 「年度がどこで決まるか」: `academic_year.py`
- 「集計はどこか」: `teacher_dashboard_service.py` / `management_dashboard_service.py`

---

## 8. 関連ドキュメント

- [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)
- [TECHNICAL_SPECIFICATION.md](./TECHNICAL_SPECIFICATION.md)
- [FEATURES.md](./FEATURES.md)
- [ER_DIAGRAM.md](./ER_DIAGRAM.md)

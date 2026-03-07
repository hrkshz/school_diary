# システム処理フロー完全ガイド

> **対象読者**: このシステムを開発した人（技術面談準備用）
> **目的**: 「処理の流れ」と「コードの場所」を即答できるようになる
> **前提知識**: WEB_DEV_BASICS.md（MVTの基本）を読んでいること
> **最終更新**: 2025-11-28

---

## 目次

1. [システム全体像（1枚図）](#1-システム全体像1枚図)
2. [リクエスト処理フロー](#2-リクエスト処理フロー)
3. [ログイン〜ダッシュボード分岐](#3-ログインダッシュボード分岐)
4. [機能×ファイル対応表](#4-機能ファイル対応表)
5. [面談対策Q&A](#5-面談対策qa)

---

## 1. システム全体像（1枚図）

**「このシステムを説明してください」と言われたらこの図を思い浮かべる**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                    【連絡帳システム 全体構成図】

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                              ユーザー
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
            ▼                    ▼                    ▼
     ┌───────────┐        ┌───────────┐        ┌───────────┐
     │   生徒    │        │   担任    │        │  管理職   │
     │           │        │           │        │校長/学年主任│
     └─────┬─────┘        └─────┬─────┘        └─────┬─────┘
           │                    │                    │
           ▼                    ▼                    ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                         【Django アプリケーション】

  ┌─────────────────────────────────────────────────────────────────────┐
  │                                                                     │
  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
  │  │  urls.py    │───►│  views.py   │───►│  templates/*.html       │ │
  │  │  (受付)     │    │  (処理)     │    │  (見た目)               │ │
  │  └─────────────┘    └──────┬──────┘    └─────────────────────────┘ │
  │                            │                                       │
  │                            ▼                                       │
  │                     ┌─────────────┐                                │
  │                     │  models.py  │                                │
  │                     │  (データ)   │                                │
  │                     └──────┬──────┘                                │
  │                            │                                       │
  └────────────────────────────┼───────────────────────────────────────┘
                               │
                               ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                     【PostgreSQL データベース】

  ┌─────────────────────────────────────────────────────────────────────┐
  │                                                                     │
  │   DiaryEntry     ClassRoom      UserProfile     TeacherNote        │
  │   (連絡帳)       (クラス)       (役割)          (担任メモ)          │
  │                                                                     │
  └─────────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### ファイル構成（実際のディレクトリ）

```
school_diary/
├── config/
│   ├── settings/          ← 設定ファイル
│   └── urls.py            ← ルートURL
│
└── school_diary/
    ├── diary/
    │   ├── models.py      ← データ定義
    │   ├── views.py       ← 処理ロジック
    │   ├── urls.py        ← アプリURL
    │   ├── adapters.py    ← ログイン後リダイレクト
    │   ├── forms.py       ← フォーム
    │   ├── alert_service.py ← 早期警告
    │   └── services/      ← ビジネスロジック
    │
    └── templates/
        └── diary/         ← HTMLテンプレート
```

---

## 2. リクエスト処理フロー

**「1回のアクセスで何が起きるか」をファイル名付きで解説**

### 例：生徒が `/diary/student/dashboard/` にアクセス

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  ┌─────────────────┐
  │   ブラウザ      │ ユーザーがURLを入力
  │  （生徒のPC）   │
  └────────┬────────┘
           │
           │ ① HTTPリクエスト「/diary/student/dashboard/ を見せて」
           ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  【config/urls.py】 ルートURL振り分け                            │
  │                                                                 │
  │  path("diary/", include("school_diary.diary.urls"))             │
  │                     ↓                                           │
  │  「/diary/...」は diary/urls.py に任せる                         │
  └────────┬────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  【diary/urls.py】 アプリURL振り分け                             │
  │                                                                 │
  │  path("student/dashboard/",                                     │
  │       views.StudentDashboardView.as_view(),                     │
  │       name="student_dashboard")                                 │
  │                     ↓                                           │
  │  「/student/dashboard/」は StudentDashboardView が担当           │
  └────────┬────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  【diary/views.py】 StudentDashboardView                        │
  │                                                                 │
  │  ② ログインチェック（LoginRequiredMixin）                        │
  │     → 未ログインなら /accounts/login/ へ強制リダイレクト          │
  │                                                                 │
  │  ③ get_context_data() でデータ取得                              │
  │     → この生徒の連絡帳を取得                                     │
  └────────┬────────────────────────────────────────────────────────┘
           │
           │ ④ データベースに問い合わせ
           ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  【diary/models.py】 DiaryEntry                                 │
  │                                                                 │
  │  DiaryEntry.objects.filter(student=self.request.user)           │
  │                     ↓                                           │
  │  「この生徒の連絡帳をください」                                   │
  └────────┬────────────────────────────────────────────────────────┘
           │
           │ ⑤ データベースからデータ取得
           ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  【PostgreSQL データベース】                                     │
  │                                                                 │
  │  diary_entry テーブルから                                        │
  │  student_id = ログインユーザーID のレコードを返す                │
  └────────┬────────────────────────────────────────────────────────┘
           │
           │ ⑥ データをViewに返す
           ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  【diary/views.py】 StudentDashboardView                        │
  │                                                                 │
  │  context["entries"] = 取得した連絡帳リスト                       │
  │  context["today_submitted"] = 今日提出済みか？                   │
  │                     ↓                                           │
  │  template_name = "diary/student_dashboard.html" に渡す           │
  └────────┬────────────────────────────────────────────────────────┘
           │
           │ ⑦ テンプレートにデータを渡す
           ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  【templates/diary/student_dashboard.html】                     │
  │                                                                 │
  │  {% for entry in entries %}                                     │
  │      {{ entry.entry_date }}                                     │
  │      {{ entry.health_condition }}                               │
  │  {% endfor %}                                                   │
  │                     ↓                                           │
  │  データをHTMLに埋め込んで完成                                    │
  └────────┬────────────────────────────────────────────────────────┘
           │
           │ ⑧ 完成したHTMLを返す
           ▼
  ┌─────────────────┐
  │   ブラウザ      │ HTMLを解釈して画面表示
  │  （生徒のPC）   │
  └─────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 ↑ これが1クリックで起きている（約0.1秒）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 処理フローまとめ表

| 順番 | 処理内容 | ファイル | 具体的なコード |
|:----:|----------|----------|---------------|
| ① | URLルーティング（ルート） | `config/urls.py` | `path("diary/", include(...))` |
| ② | URLルーティング（アプリ） | `diary/urls.py` | `path("student/dashboard/", ...)` |
| ③ | ログインチェック | `diary/views.py` | `LoginRequiredMixin` |
| ④ | データ取得処理 | `diary/views.py` | `get_context_data()` |
| ⑤ | DB問い合わせ | `diary/models.py` | `DiaryEntry.objects.filter()` |
| ⑥ | テンプレート描画 | `templates/diary/*.html` | `{{ entry.xxx }}` |

---

## 3. ログイン〜ダッシュボード分岐

**「役割によってどこに行くか」と「その処理がどこに書かれているか」**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

              【ログイン〜ダッシュボード分岐フロー】

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                        ユーザーがログイン
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  【allauth】ログイン処理                                             │
│                                                                     │
│   /accounts/login/ でID/パスワード認証                              │
│                              │                                      │
│                              ▼                                      │
│   認証成功 → get_login_redirect_url() を呼び出し                    │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│  【diary/adapters.py】 RoleBasedRedirectAdapter                     │
│                                                                     │
│   get_login_redirect_url(request) メソッド                          │
│                              │                                      │
│                              ▼                                      │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │  役割判定ロジック（優先順位順）                            │     │
│   │                                                          │     │
│   │  if user.is_superuser:        → /admin/                  │     │
│   │  if profile.role == "school_leader": → school_overview   │     │
│   │  if profile.role == "grade_leader":  → grade_overview    │     │
│   │  if profile.role == "teacher":       → teacher_dashboard │     │
│   │  else (生徒):                        → student_dashboard │     │
│   └──────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────┬───────────┼───────────┬───────────┐
        │           │           │           │           │
        ▼           ▼           ▼           ▼           ▼
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                        5つのリダイレクト先
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  管理者(1)  │ │  校長(2)    │ │ 学年主任(3) │ │  担任(4)    │ │  生徒(5)    │
├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────┤
│  /admin/    │ │/diary/      │ │/diary/      │ │/diary/      │ │/diary/      │
│             │ │school-      │ │grade-       │ │teacher/     │ │student/     │
│             │ │overview/    │ │overview/    │ │dashboard/   │ │dashboard/   │
├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────┤ ├─────────────┤
│Django管理   │ │SchoolOver-  │ │GradeOver-   │ │TeacherDash- │ │StudentDash- │
│画面(組込)   │ │viewView     │ │viewView     │ │boardView    │ │boardView    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
       │               │               │               │               │
       ▼               ▼               ▼               ▼               ▼
 ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
 │できること │  │できること │  │できること │  │できること │  │できること │
 ├───────────┤  ├───────────┤  ├───────────┤  ├───────────┤  ├───────────┤
 │・全データ │  │・学校全体 │  │・学年全体 │  │・クラスの │  │・自分の   │
 │  管理     │  │  の統計   │  │  の統計   │  │  生徒一覧 │  │  連絡帳   │
 │・ユーザー │  │・学年比較 │  │・クラス   │  │・連絡帳   │  │・作成     │
 │  作成     │  │・緊急     │  │  比較     │  │  閲覧     │  │・編集     │
 │・クラス   │  │  アラート │  │・エスカ   │  │・既読処理 │  │・履歴     │
 │  管理     │  │           │  │  レーション│  │・アラート │  │  閲覧     │
 └───────────┘  └───────────┘  └───────────┘  └───────────┘  └───────────┘
```

### 役割判定のコード

**ファイル**: `diary/adapters.py`
**クラス**: `RoleBasedRedirectAdapter`
**メソッド**: `get_login_redirect_url()`

```python
def get_login_redirect_url(self, request):
    user = request.user

    # ① 管理者チェック（最優先）
    if user.is_superuser:
        return "/admin/"

    # プロファイルを取得
    profile = getattr(user, "profile", None)

    if profile:
        # ② 校長/教頭
        if profile.role == "school_leader":
            return reverse("diary:school_overview")

        # ③ 学年主任
        if profile.role == "grade_leader":
            return reverse("diary:grade_overview")

        # ④ 担任
        if profile.role == "teacher" or user.homeroom_classes.exists():
            return reverse("diary:teacher_dashboard")

    # ⑤ 生徒（デフォルト）
    return reverse("diary:student_dashboard")
```

---

## 4. 機能×ファイル対応表

**「〇〇はどこですか？」に即答するための一覧表**

### 4.1 認証・権限

| 機能 | ファイル | クラス/関数 |
|------|----------|------------|
| ログイン後の振り分け | `adapters.py` | `RoleBasedRedirectAdapter.get_login_redirect_url()` |
| 役割の定義 | `models.py` | `UserProfile.ROLE_CHOICES` |
| ログインチェック | `views.py` | `LoginRequiredMixin`（各Viewに継承） |
| 権限チェック（他人の連絡帳） | `views.py` | `DiaryUpdateView.get_object()` |

### 4.2 生徒機能

| 機能 | ファイル | クラス/関数 | URL |
|------|----------|------------|-----|
| 生徒ダッシュボード | `views.py` | `StudentDashboardView` | `/diary/student/dashboard/` |
| 連絡帳作成 | `views.py` | `DiaryCreateView` | `/diary/create/` |
| 連絡帳編集 | `views.py` | `DiaryUpdateView` | `/diary/diary/<id>/edit/` |
| 過去履歴一覧 | `views.py` | `DiaryHistoryView` | `/diary/history/` |

### 4.3 担任機能

| 機能 | ファイル | クラス/関数 | URL |
|------|----------|------------|-----|
| 担任ダッシュボード | `views.py` | `TeacherDashboardView` | `/diary/teacher/dashboard/` |
| 個別生徒詳細 | `views.py` | `TeacherStudentDetailView` | `/diary/teacher/student/<id>/` |
| 既読処理 | `views.py` | `teacher_mark_as_read()` | `/diary/teacher/diary/<id>/mark-as-read/` |
| クラス健康状態 | `views.py` | `ClassHealthDashboardView` | `/diary/teacher/class-health/` |
| 担任メモ追加 | `views.py` | `teacher_add_note()` | `/diary/teacher/note/add/<id>/` |
| 出席記録 | `views.py` | `teacher_save_attendance()` | `/diary/teacher/attendance/save/` |

### 4.4 管理職機能

| 機能 | ファイル | クラス/関数 | URL |
|------|----------|------------|-----|
| 学年概要（学年主任） | `views.py` | `GradeOverviewView` | `/diary/grade-overview/` |
| 学校概要（校長） | `views.py` | `SchoolOverviewView` | `/diary/school-overview/` |

### 4.5 早期警告（アラート）

| 機能 | ファイル | クラス/関数 |
|------|----------|------------|
| 生徒分類（6カテゴリ） | `alert_service.py` | `classify_students()` |
| メンタル★1検出 | `utils.py` | `check_critical_mental_state()` |
| 3日連続低下検出 | `utils.py` | `check_consecutive_decline()` |
| クラス5人以上不調 | `views.py` | `TeacherDashboardView.get_context_data()` |

### 4.6 データモデル

| モデル | 役割 | 主なフィールド |
|--------|------|---------------|
| `DiaryEntry` | 連絡帳 | student, entry_date, health_condition, mental_condition, reflection, is_read |
| `ClassRoom` | クラス | grade, class_name, homeroom_teacher, students |
| `UserProfile` | ユーザー役割 | user, role, managed_grade |
| `TeacherNote` | 担任メモ | teacher, student, note, is_shared |
| `DailyAttendance` | 出席記録 | student, date, status, absence_reason |

---

## 5. 面談対策Q&A

### 5.1 よく聞かれる質問と回答テンプレート

| 質問 | 回答テンプレート |
|------|-----------------|
| **「システム全体を説明してください」** | 「連絡帳システムは、生徒が毎日の体調・メンタル・振り返りを記録し、担任が確認するWebアプリです。Djangoで構築し、役割（生徒/担任/学年主任/校長）ごとに異なるダッシュボードを表示します。早期警告機能でメンタル低下を自動検出します。」 |
| **「ログイン後の振り分けはどこ？」** | 「`adapters.py` の `RoleBasedRedirectAdapter` です。`get_login_redirect_url()` でユーザーの役割を判定し、適切なダッシュボードにリダイレクトしています。」 |
| **「連絡帳の保存はどこ？」** | 「`views.py` の `DiaryCreateView.form_valid()` です。内部で `DiaryEntryService.create_entry()` を呼び出して保存しています。」 |
| **「権限チェックはどこ？」** | 「`views.py` の各Viewで行っています。`LoginRequiredMixin` でログインチェック、`get_object()` で所有者チェックをしています。他人の連絡帳にアクセスしたら `PermissionDenied` を投げます。」 |
| **「早期警告はどこ？」** | 「`alert_service.py` の `classify_students()` と、`utils.py` の `check_critical_mental_state()` です。メンタル★1や3日連続低下を自動検出します。」 |
| **「役割はどこで定義？」** | 「`models.py` の `UserProfile.ROLE_CHOICES` で5種類（admin, student, teacher, grade_leader, school_leader）を定義しています。」 |
| **「MVTを説明してください」** | 「Model（models.py）がデータの形、View（views.py）が処理ロジック、Template（*.html）が見た目を担当します。分離することで、見た目だけ変えたいときはTemplateだけ、処理だけ変えたいときはViewだけ修正できます。」 |

### 5.2 説明練習用チェックリスト

**図1を見ながら**:
- [ ] 「URLにアクセスすると、urls.py → views.py → models.py → template の順で処理される」と説明できる
- [ ] 各ステップのファイル名を言える

**図2を見ながら**:
- [ ] 「ログイン後は adapters.py で役割を判定する」と説明できる
- [ ] 5つの役割とリダイレクト先を言える

**図3を見ながら**:
- [ ] 「連絡帳作成は views.py の DiaryCreateView」と即答できる
- [ ] 「既読処理は views.py の teacher_mark_as_read()」と即答できる
- [ ] 「早期警告は alert_service.py」と即答できる

---

## 関連ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| `WEB_DEV_BASICS.md` | Web開発の基礎（MVTとは何か） |
| `FILE_REFERENCE.md` | 各ファイルの詳細な役割 |
| `SYSTEM_ARCHITECTURE.md` | システム設計の詳細 |
| `INTERVIEW_QA.md` | 技術面談の想定問答 |

---

**作成日**: 2025-11-28
**用途**: 技術面談準備・コード理解用

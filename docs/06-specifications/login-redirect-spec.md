# 機能仕様書（As-Built）: ログインリダイレクト機能

> **作成日**: 2025-10-22
> **対象バージョン**: v0.3.0-map
> **ステータス**: As-Built（実装済み仕様）

---

## 概要

ユーザーがログイン後、役割（role）に応じて適切なダッシュボード画面に自動的にリダイレクトする。

### 目的
- ユーザーが最も頻繁に使う画面に直接遷移
- 役割に応じた適切な情報を表示

---

## ファイル構成

| ファイル | 役割 |
|---------|------|
| models.py | 役割の定義（UserProfile.ROLE_CHOICES） |
| adapters.py | リダイレクトルール（RoleBasedRedirectAdapter） |
| views.py | 各ダッシュボードの実装 |

---

## リダイレクト優先順位

上から順にチェックし、最初にマッチした条件で決定する。

| 優先度 | 条件 | リダイレクト先 | 画面の役割 | コード参照 |
|-------|------|-------------|----------|----------|
| 1 | `is_superuser=True` | `/admin/` | Django管理画面 | adapters.py (get_login_redirect_url) |
| 2 | `profile.role='school_leader'` | `/school-overview/` | 学校全体統括 | adapters.py (get_login_redirect_url), views.py (SchoolOverviewView) |
| 3 | `profile.role='grade_leader'` | `/grade-overview/` | 学年全体比較 | adapters.py (get_login_redirect_url), views.py (GradeOverviewView) |
| 4 | `profile.role='teacher'` または `homeroom_classes`が存在 | `/teacher/` | 担任用 | adapters.py (get_login_redirect_url), views.py (TeacherDashboardView) |
| 5 | 上記以外（デフォルト） | `/student/` | 生徒用 | adapters.py (get_login_redirect_url), views.py (StudentDashboardView) |

---

## 各ロールの詳細

### 1. システム管理者（admin）

**条件**: `is_superuser=True`

**リダイレクト先**: `/admin/`

**画面の役割**: Django標準の管理画面

**理由**: システム全体を管理する必要があるため

**コード参照**:
- 判定: adapters.py (get_login_redirect_url)
- ロール定義: models.py (UserProfile.ROLE_CHOICES)

---

### 2. 校長/教頭（school_leader）

**条件**: `profile.role='school_leader'`

**リダイレクト先**: `/school-overview/`

**画面の役割**: 学校全体の統括（全学年の統計表示）

**表示情報**:
- 全学年の統計（提出率、欠席者数、体調不良者数）
- 学級閉鎖判断の基礎データ

**コード参照**:
- 判定: adapters.py (get_login_redirect_url)
- ロール定義: models.py (UserProfile.ROLE_CHOICES)
- 画面実装: views.py (SchoolOverviewView)

---

### 3. 学年主任（grade_leader）

**条件**: `profile.role='grade_leader'`

**リダイレクト先**: `/grade-overview/`

**画面の役割**: 学年全体の比較（管理学年の全クラスを表示）

**表示情報**:
- 学年内のクラス比較
- 学年全体の統計

**注意**: `managed_grade`フィールドで管理する学年を設定

**コード参照**:
- 判定: adapters.py (get_login_redirect_url)
- ロール定義: models.py (UserProfile.ROLE_CHOICES, managed_grade)
- 画面実装: views.py (GradeOverviewView)

---

### 4. 担任（teacher）

**条件**:
- `profile.role='teacher'` **または**
- `homeroom_classes`が存在する

**リダイレクト先**: `/teacher/`

**画面の役割**: 担任用ダッシュボード（自分のクラスの生徒管理）

**表示情報**:
- 生徒一覧、未読件数
- 体調・メンタルの状態
- 早期警告アラート

**例外ケース**: `profile.role`が未設定でも、`homeroom_classes`があれば担任ダッシュボードへリダイレクト（既存ユーザー互換性）

**コード参照**:
- 判定: adapters.py (get_login_redirect_url)
- ロール定義: models.py (UserProfile.ROLE_CHOICES)
- 画面実装: views.py (TeacherDashboardView)

---

### 5. 生徒（student）

**条件**: 上記の1〜4に該当しない場合（デフォルト）

**リダイレクト先**: `/student/`

**画面の役割**: 生徒用ダッシュボード（自分の連絡帳の記入・確認）

**表示情報**:
- 自分の過去7日分の連絡帳
- 提出リマインダー

**コード参照**:
- 判定: adapters.py (get_login_redirect_url)
- ロール定義: models.py (UserProfile.ROLE_CHOICES, default='student')
- 画面実装: views.py (StudentDashboardView)

---

## 例外ケース

### プロファイルが存在しない場合

**状況**: `user.profile`が存在しない

**処理**:
- 担任登録（`homeroom_classes`）あり → 担任ダッシュボードへ
- 担任登録なし → 生徒ダッシュボードへ

**理由**: 既存ユーザーとの互換性を保つため

**コード参照**: adapters.py (get_login_redirect_url)

---

### 複数ロール兼任時の優先順位

**状況**: 校長が担任も兼任している場合

**処理**: 上位の役割が優先される（校長 > 学年主任 > 担任）

**理由**: より広い範囲を管理する役割を優先

**コード参照**: adapters.py (get_login_redirect_url)

---

## ロール定義

### ROLE_CHOICES

```python
ROLE_CHOICES = [
    ("admin", "システム管理者"),
    ("student", "生徒"),
    ("teacher", "担任"),
    ("grade_leader", "学年主任"),
    ("school_leader", "教頭/校長"),
]
```

**データ構造**: `(内部コード, 表示名)`のペア

**コード参照**: models.py (UserProfile.ROLE_CHOICES)

---

### TEACHER_ROLES

```python
TEACHER_ROLES = [ROLE_TEACHER, ROLE_GRADE_LEADER, ROLE_SCHOOL_LEADER]
```

**意味**: 担任、学年主任、校長は全員「先生」= 連絡帳を読む権限がある

**コード参照**: models.py (UserProfile.TEACHER_ROLES)

---

## 実装の流れ

```
1. ユーザーがログイン
   ↓
2. adapters.py が role をチェック
   ↓
3. models.py から role 情報を取得
   ↓
4. adapters.py が適切なURLにリダイレクト
   ↓
5. views.py の対応するダッシュボードを表示
```

---

## 変更履歴

| 日付 | 変更内容 | 理由 | コミット |
|------|---------|------|---------|
| 2025-10-22 | `is_staff` → `is_superuser` に変更 | 学年主任が管理画面にリダイレクトされるバグ修正 | 34de710 |

---

## 関連情報

### 関連ファイル
- adapters.py
- models.py
- views.py

### テストケース
- school_diary/diary/test_admin_user_creation.py

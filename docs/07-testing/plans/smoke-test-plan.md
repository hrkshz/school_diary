# Smoke Test Plan - ログインリダイレクト修正後の動作確認

## 📋 テスト概要

| 項目 | 内容 |
|-----|------|
| **テスト名** | Smoke Test - Role-based Login Redirect |
| **テストレベル** | System Test（システムテスト） |
| **テスト種類** | Smoke Test / Regression Test |
| **目的** | バグ修正後の基本動作確認（各ロールのログイン・リダイレクト） |
| **対象機能** | ユーザー認証、ロールベースリダイレクト |
| **実施想定時間** | 10-15分 |
| **担当** | QAエンジニア |

## 🎯 テスト目的

### 背景

**修正前の問題**:
- 学年主任がログイン後、学年ダッシュボードではなく管理画面（/admin/）にリダイレクトされる
- 原因: `adapters.py`で`is_staff`チェックが`role`チェックより優先されていた

**修正内容**:
- `school_diary/diary/adapters.py:82-84`を修正
- `if user.is_staff:` → `if user.is_superuser:` に変更
- システム管理者（is_superuser=True）のみ /admin/ にリダイレクト
- その他のロールはroleに基づいてリダイレクト

**テスト目的**:
1. 修正が正しく動作することを確認
2. 他のロール（生徒、担任、校長）が影響を受けていないことを確認（回帰テスト）
3. 実際のブラウザ環境での動作確認（Unit Testでは確認できない部分）

## 🔍 テストスコープ

### テスト対象（In Scope）

- ✅ 各ロールのログイン機能
- ✅ ログイン後のリダイレクト先
- ✅ リダイレクト先ページの表示確認

### テスト対象外（Out of Scope）

- ❌ 各ダッシュボードの詳細機能
- ❌ データの編集・削除機能
- ❌ パフォーマンステスト
- ❌ セキュリティテスト（別途実施）

## 🧪 テストケース

### TC-001: システム管理者（is_superuser=True）のログイン

**事前条件**:
- システム管理者ユーザーが存在する
- Docker環境が起動している（`dc up -d`）

**テスト手順**:
1. ブラウザで http://localhost:8000 にアクセス
2. ログインページにリダイレクトされることを確認
3. システム管理者の認証情報でログイン
   - Email: `admin@example.com`
   - Password: `password123`
4. リダイレクト先を確認

**期待結果**:
- ✅ `/admin/` にリダイレクトされる
- ✅ Django管理画面が表示される
- ✅ 上部に「Django administration」のヘッダーが表示される

**優先度**: High
**カテゴリ**: Smoke Test

---

### TC-002: 学年主任（role='grade_leader'）のログイン

**事前条件**:
- 学年主任ユーザーが存在する（管理画面で作成済み）
- is_staff=True（管理画面で作成したため）
- is_superuser=False

**テスト手順**:
1. ブラウザで http://localhost:8000 にアクセス
2. ログインページにリダイレクトされることを確認
3. 学年主任の認証情報でログイン
   - Email: （管理画面で作成したユーザーのメールアドレス）
   - Password: `password123`
4. リダイレクト先を確認

**期待結果**:
- ✅ `/grade-overview/` にリダイレクトされる（**/admin/ ではない**）
- ✅ 学年ダッシュボードが表示される
- ✅ 「学年概況」「共有アラート」などのセクションが表示される

**優先度**: Critical（今回の修正対象）
**カテゴリ**: Regression Test

---

### TC-003: 担任（role='teacher'）のログイン

**事前条件**:
- 担任ユーザーが存在する
- ClassRoomが作成され、homeroom_teacherとして登録されている

**テスト手順**:
1. ブラウザで http://localhost:8000 にアクセス
2. ログインページにリダイレクトされることを確認
3. 担任の認証情報でログイン
   - Email: `approver@example.com`（setup_devで作成）
   - Password: `password123`
4. リダイレクト先を確認

**期待結果**:
- ✅ `/teacher/` にリダイレクトされる（**/admin/ ではない**）
- ✅ 担任ダッシュボードが表示される
- ✅ 「要確認」「未提出」などのアラートが表示される

**優先度**: High
**カテゴリ**: Regression Test

---

### TC-004: 生徒（role='student'）のログイン

**事前条件**:
- 生徒ユーザーが存在する
- is_staff=False

**テスト手順**:
1. ブラウザで http://localhost:8000 にアクセス
2. ログインページにリダイレクトされることを確認
3. 生徒の認証情報でログイン
   - Email: `user@example.com`（setup_devで作成）
   - Password: `password123`
4. リダイレクト先を確認

**期待結果**:
- ✅ `/student/` にリダイレクトされる
- ✅ 生徒ダッシュボードが表示される
- ✅ 連絡帳提出フォームが表示される

**優先度**: Medium
**カテゴリ**: Regression Test

---

### TC-005: 校長/教頭（role='school_leader'）のログイン

**事前条件**:
- 校長/教頭ユーザーが存在する

**テスト手順**:
1. ブラウザで http://localhost:8000 にアクセス
2. ログインページにリダイレクトされることを確認
3. 校長/教頭の認証情報でログイン
   - Email: （管理画面で作成したユーザーのメールアドレス）
   - Password: `password123`
4. リダイレクト先を確認

**期待結果**:
- ✅ `/school-overview/` にリダイレクトされる（**/admin/ ではない**）
- ✅ 学校全体ダッシュボードが表示される
- ✅ 学校全体の統計情報が表示される

**優先度**: Medium
**カテゴリ**: Regression Test

---

## 🧰 テスト環境

### 必須環境

- **OS**: Ubuntu 22.04 (WSL2)
- **ブラウザ**: Chrome 最新版（推奨）、Firefox、Safari
- **Docker**: 起動済み（`dc up -d`）
- **アクセスURL**: http://localhost:8000

### テストデータ

| ロール | Email | Password | 作成方法 |
|-------|-------|----------|---------|
| システム管理者 | admin@example.com | password123 | setup_dev |
| 学年主任 | （管理画面で作成） | password123 | 管理画面 |
| 担任 | approver@example.com | password123 | setup_dev |
| 生徒 | user@example.com | password123 | setup_dev |
| 校長/教頭 | （管理画面で作成） | password123 | 管理画面 |

**注意**: 学年主任・校長/教頭がいない場合は、管理画面で作成する。

## ✅ 合格基準

### Pass条件

- 全テストケース（TC-001〜TC-005）がPass
- 特に**TC-002（学年主任）**が必ずPass（今回の修正対象）
- 期待結果と実際の結果が完全一致

### Fail条件

- いずれかのテストケースがFail
- 特に**TC-002（学年主任）**がFailの場合は即座に開発チームに報告

### Blocked条件

- テスト実施不可（Docker起動できない、ユーザーが存在しないなど）

## 📊 テスト結果記録

テスト実施後、以下のファイルに結果を記録：

`docs/testing/results/YYYYMMDD-smoke-test-result.md`

**記録必須項目**:
- 実施日時
- 実施者
- 各テストケースの結果（Pass/Fail/Blocked）
- スクリーンショット（重要な画面のみ）
- バグ発見時の詳細情報

## 🐛 バグ発見時の対応

### バグレポートに含める情報

1. **テストケース番号**: TC-XXX
2. **再現手順**: 詳細な手順
3. **期待結果**: 〇〇が表示される
4. **実際の結果**: ××が表示された
5. **スクリーンショット**: `screenshots/YYYYMMDD/tc-XXX-fail.png`
6. **環境情報**: ブラウザ、OS、バージョン
7. **重要度**: Critical/High/Medium/Low

### 報告先

- GitHub/GitLab Issue
- 開発チームSlack/メール

## 📝 備考

- このテストは**修正後の最初の確認**です
- Unit Test（pytest）では既に修正が正しいことを確認済み
- このSmoke Testは「実際のブラウザ環境での動作確認」が目的
- Pass後、より詳細なCritical Path Testを実施予定

## 📚 関連ドキュメント

- [修正コミット](../../../school_diary/diary/adapters.py) - adapters.py:82-84
- [Unit Test](../../../school_diary/diary/test_admin_user_creation.py) - test_grade_leader_with_is_staff_login_redirect
- [USER_TESTING_MANUAL.md](../../../USER_TESTING_MANUAL.md) - テストユーザー情報

---

**作成日**: 2025-10-22
**最終更新**: 2025-10-22
**作成者**: QAチーム
**承認者**: -
**バージョン**: 1.0

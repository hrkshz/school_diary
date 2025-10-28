# E2Eテスト計画書

作成日: 2025-10-28
対象システム: 連絡帳管理システム
バージョン: v0.3.0-map

---

## 目的

ブラウザでの実際の動作を確認し、Pytestではカバーできないフロントエンド機能（JavaScript、AJAX、画面遷移）をテストする。

テスト実行と同時にスクリーンショットを撮影し、ユーザーマニュアルを自動生成する。

---

## テスト環境

- テストツール: Playwright
- ブラウザ: Chromium
- テスト対象URL: http://localhost:8000
- 実行環境: Docker (Django + PostgreSQL)

---

## テスト対象

### 対象ロール（5種類）

1. 生徒
2. 担任
3. 学年主任
4. 教頭/校長
5. 管理者

### 対象機能

| 機能分類 | 画面ID | 画面名 | テストケースID |
|---------|-------|--------|--------------|
| 認証 | AUTH-001 | ログイン | TC-AUTH-001-01〜05 |
| 生徒 | STU-001 | 生徒ダッシュボード | TC-STU-001-01 |
| 生徒 | STU-002 | 連絡帳作成 | TC-STU-002-01 |
| 生徒 | STU-003 | 連絡帳編集 | TC-STU-003-01 |
| 担任 | TEA-001 | 担任ダッシュボード | TC-TEA-001-01 |
| 担任 | TEA-ACT-001 | 既読処理 | TC-TEA-ACT-001-01 |
| 担任 | TEA-ACT-003 | メモ追加 | TC-TEA-ACT-003-01 |
| 学年主任 | GRD-001 | 学年統計 | TC-GRD-001-01 |
| 教頭/校長 | SCH-001 | 学校統計 | TC-SCH-001-01 |
| 管理者 | ADM-001 | 管理画面 | TC-ADM-001-01 |
| セキュリティ | - | 権限チェック | TC-SEC-001, TC-SEC-002 |

---

## テストケース詳細

### 認証テスト

**TC-AUTH-001-01: 生徒ログイン**
- 手順: ログイン画面からstudent_1_a_01@example.comでログイン
- 期待結果: 生徒ダッシュボード(/diary/student/dashboard/)にリダイレクト

**TC-AUTH-001-02: 担任ログイン**
- 手順: ログイン画面からteacher_1_a@example.comでログイン
- 期待結果: 担任ダッシュボード(/diary/teacher/dashboard/)にリダイレクト

**TC-AUTH-001-03: 学年主任ログイン**
- 手順: 学年主任権限を持つアカウントでログイン
- 期待結果: 学年統計画面またはダッシュボードにリダイレクト

**TC-AUTH-001-04: 教頭/校長ログイン**
- 手順: 校長権限を持つアカウントでログイン
- 期待結果: 学校統計画面にアクセス可能

**TC-AUTH-001-05: 管理者ログイン**
- 手順: admin@example.comでログイン
- 期待結果: 管理画面(/admin/)にリダイレクト

### 生徒機能テスト

**TC-STU-002-01: 連絡帳作成**
- 手順: 生徒ダッシュボードから新規連絡帳作成
- 入力: 体調（良好）、メンタル（4）、振り返り（テスト内容）
- 期待結果: 連絡帳が作成され、ダッシュボードに表示される

**TC-STU-003-01: 連絡帳編集**
- 手順: 作成した連絡帳を編集
- 期待結果: 既読前であれば編集可能

### 担任機能テスト

**TC-TEA-ACT-001-01: 既読処理**
- 手順: 生徒詳細画面から連絡帳を既読にする
- 入力: 反応（絵文字）、対応記録（任意）
- 期待結果: 既読状態が保存される

**TC-TEA-ACT-003-01: 担任メモ追加**
- 手順: 生徒詳細画面からメモを追加
- 入力: メモ内容、学年共有フラグ（任意）
- 期待結果: メモが保存される

### セキュリティテスト

**TC-SEC-001: 他クラスの連絡帳アクセス**
- 手順: 担任Aが担任Bのクラスの生徒詳細URLに直接アクセス
- 期待結果: 403エラーまたはリダイレクト

**TC-SEC-002: 他担任のメモアクセス**
- 手順: 担任Aが担任Bのメモ編集URLに直接アクセス
- 期待結果: 403エラーまたはリダイレクト

---

## 実行手順

```bash
# 1. Dockerコンテナ起動
docker compose -f local.yml up -d

# 2. Playwrightブラウザインストール（初回のみ）
npx playwright install chromium --with-deps

# 3. テスト実行
npx playwright test

# 4. マニュアル生成
node scripts/generate-manuals.js

# 5. レポート確認
npx playwright show-report
```

---

## 成果物

### テスト結果
- HTMLレポート: playwright-report/index.html
- JSON結果: test-results.json
- スクリーンショット: tests/e2e/screenshots/

### ユーザーマニュアル（自動生成）
- 生徒用: doc/MANUALS/01_STUDENT.md
- 担任用: doc/MANUALS/02_TEACHER.md
- 学年主任用: doc/MANUALS/03_GRADE_LEADER.md
- 教頭/校長用: doc/MANUALS/04_PRINCIPAL.md
- 管理者用: doc/MANUALS/05_ADMIN.md

---

## 備考

### マニュアル自動生成の仕組み

テスト実行時に`manual-recorder.js`フィクスチャが各ステップでスクリーンショットを撮影し、ステップ情報（タイトル、説明文、画像パス）をJSONに保存する。

テスト完了後、`scripts/generate-manuals.js`がJSONを読み込んでMarkdownマニュアルを生成する。

### テストアカウント

詳細は [TEST_ACCOUNTS.md](TEST_ACCOUNTS.md) を参照。

---

最終更新: 2025-10-28

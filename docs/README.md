# 連絡帳管理システム - ドキュメント

> **プロジェクト名**: 連絡帳管理システム（school_diary）
> **バージョン**: v0.3.0-map
> **作成日**: 2025-10-23
> **本番環境**: https://d2wk3j2pacp33b.cloudfront.net

---

## 📚 ドキュメント一覧

このドキュメントは **評価者向け** に整理されています。
**01 から順に読む**と、システム全体を理解できます。

### 必須ドキュメント（評価対象）

| No  | ドキュメント                                | 概要               | 所要時間 |
| --- | ------------------------------------------- | ------------------ | -------- |
| 01  | [要件定義書](01-requirements.md)            | 課題内容・要件     | 5 分     |
| 02  | [システム概要](02-system-overview.md)       | 何を作ったか       | 3 分     |
| 03  | [機能一覧](03-features.md)                  | 何ができるか       | 5 分     |
| 04  | [データモデル設計書](04-data-model.md)      | DB 構造（ER 図）   | 10 分    |
| 05  | [アーキテクチャ設計書](05-architecture.md)  | 技術スタック・構成 | 10 分    |
| 06  | [主要機能仕様書](06-specifications/)        | 重要機能の詳細     | 10 分    |
| 07  | [テスト戦略・結果](07-testing/)             | 品質保証           | 5 分     |
| 08  | [デプロイ手順書](08-deployment.md)          | 環境構築手順       | 5 分     |
| 09  | [テストアカウント一覧](09-test-accounts.md) | ログイン情報       | 2 分     |

**合計所要時間**: 約 55 分

---

## 🚀 クイックスタート（評価者向け）

### Step 1: 本番環境にアクセス

```
URL: https://d2wk3j2pacp33b.cloudfront.net
```

### Step 2: テストアカウントでログイン

| ロール   | メールアドレス             | パスワード  |
| -------- | -------------------------- | ----------- |
| 管理者   | admin@example.com          | password123 |
| 学年主任 | grade_leader@example.com   | password123 |
| 担任     | teacher_1_a@example.com    | password123 |
| 生徒     | student_1_a_01@example.com | password123 |

詳細: [09-test-accounts.md](09-test-accounts.md)

### Step 3: 主要機能を試す

1. **生徒ロール**: 連絡帳作成・提出
2. **担任ロール**: 連絡帳確認・既読処理・反応追加
3. **学年主任ロール**: 学年全体の統計確認・共有メモ作成
4. **管理者ロール**: 管理画面（/admin/）でデータ管理

---

## 📖 読む順序（推奨）

### 初めて見る方（評価者）

1. **[02-system-overview.md](02-system-overview.md)** - システム概要（3 分）
2. **[03-features.md](03-features.md)** - 機能一覧（5 分）
3. **本番環境でログイン** - 実際に触る（10 分）
4. **[04-data-model.md](04-data-model.md)** - ER 図確認（10 分）
5. **[07-testing/](07-testing/)** - テスト結果確認（5 分）

**合計**: 約 30 分でシステム全体を把握

### 技術詳細を知りたい方

1. **[05-architecture.md](05-architecture.md)** - アーキテクチャ設計書（10 分）
2. **[06-specifications/](06-specifications/)** - 主要機能仕様書（10 分）
3. **[08-deployment.md](08-deployment.md)** - デプロイ手順書（5 分）

---

## 🎯 実装機能

### 基本機能

- ロール別ダッシュボード（5ロール: 生徒、担任、学年主任、校長/教頭、システム管理者）
- 連絡帳作成・編集・提出・既読処理
- 管理画面（Django Admin）
- ユーザー管理、クラス管理

### 担任機能

- Inbox Pattern（6カテゴリ分類: P0重要、P1要注意、未提出、未読、反応待ち、完了済み）
- 早期警告システム（3日連続メンタル低下検知、メンタル★1即時アラート）
- クラス健康ダッシュボード（7日/14日ヒートマップ）
- 反応・対応記録（生徒への反応と内部対応の分離）
- 出席記録管理

### 学年/学校機能

- 担任間共有メモ（学年共有、既読管理）
- 学年統計（クラス比較、メンタル推移）
- 学校統計（学級閉鎖判断支援）

### QA Phase（品質保証）

- 単体テスト: 150件合格（pytest、自動化）
- 機能テスト: 53件合格（Feature Tests）
- 総合評価: A (90/100)、判定: デプロイ可能
- 詳細: [07-testing/](07-testing/)

---

## 🏗️ 技術スタック

- **言語**: Python 3.12
- **FW**: Django 5.x
- **DB**: PostgreSQL 16
- **インフラ**: AWS（EC2, RDS, CloudFront）
- **IaC**: Terraform
- **依存管理**: uv + pyproject.toml
- **品質保証**: pytest, Ruff, mypy

---

## 📂 ディレクトリ構造

```
docs/
├── README.md                    # このファイル
│
├── 01-requirements.md           # 要件定義書
├── 02-system-overview.md        # システム概要
├── 03-features.md               # 機能一覧
├── 04-data-model.md             # データモデル設計書
├── 05-architecture.md           # アーキテクチャ設計書
│
├── 06-specifications/           # 主要機能仕様書
│   └── login-redirect-spec.md
│
├── 07-testing/                  # テスト戦略・結果
│   ├── README.md
│   ├── plans/
│   │   └── smoke-test-plan.md
│   └── results/
│       └── 20251022-smoke-test-result.md
│
├── 08-deployment.md             # デプロイ手順書
├── 09-test-accounts.md          # テストアカウント一覧

```

---

## 🔗 関連ドキュメント

### ルートディレクトリ

| ドキュメント                          | 説明                      |
| ------------------------------------- | ------------------------- |
| [../README.md](../README.md)          | プロジェクト全体の README |
| [../PROJECT_INFO.md](PROJECT_INFO.md) | プロジェクト情報          |
| [../COMMANDS.md](COMMANDS.md)         | よく使うコマンド          |

---

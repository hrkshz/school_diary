# デプロイ手順書

> **作成日**: 2025-10-23
> **対象バージョン**: v0.3.0-map
> **ステータス**: As-Built

---

## 概要

連絡帳管理システムのデプロイ手順書。

### デプロイオプション

| 環境 | 状態 | URL |
|-----|------|-----|
| **本番環境（AWS）** | 稼働中 | https://d2wk3j2pacp33b.cloudfront.net |
| **ローカル環境** | 開発用 | http://localhost:8000 |

---

## 本番環境（AWS）

### 構成

- **EC2**: t2.medium（Django + Gunicorn）
- **RDS**: PostgreSQL 16
- **CloudFront**: CDN
- **ACM**: SSL/TLS証明書
- **Terraform**: インフラ管理

### アクセス

```
URL: https://d2wk3j2pacp33b.cloudfront.net
```

**詳細**: `docs-private/aws/` 配下のドキュメントを参照

---

## ローカル環境構築手順

### 前提条件

- Docker Desktop インストール済み
- Git インストール済み
- WSL2（Windowsの場合）

### Step 1: リポジトリクローン

```bash
git clone https://gitlab.com/your-org/quest_1.git
cd quest_1
```

### Step 2: 環境変数設定

```bash
# .envs/.local/.django を確認
# デフォルトで開発用設定が入っている
```

### Step 3: Docker起動

```bash
# エイリアス設定（推奨）
alias dc='docker compose -f docker-compose.local.yml'
alias dj='docker compose -f docker-compose.local.yml run --rm django python manage.py'

# コンテナ起動
dc up -d
```

### Step 4: マイグレーション

```bash
dj migrate
```

### Step 5: テストユーザー作成

```bash
dj setup_dev
```

### Step 6: アクセス

```
開発サーバー: http://localhost:8000
管理画面: http://localhost:8000/admin
Mailpit: http://localhost:8025
```

### テストアカウント

| ロール | メールアドレス | パスワード |
|--------|--------------|-----------|
| 管理者 | admin@example.com | password123 |
| 学年主任 | grade_leader@example.com | password123 |
| 担任 | teacher_1_a@example.com | password123 |
| 生徒 | student_1_a_01@example.com | password123 |

詳細: `docs/09-test-accounts.md`

---

## トラブルシューティング

### ポート衝突

```bash
# ポート使用状況確認
sudo lsof -i :8000

# 既存コンテナ停止
dc down
```

### データベース接続エラー

```bash
# PostgreSQLコンテナ確認
dc ps postgres

# ログ確認
dc logs postgres
```

### 依存関係エラー

```bash
# イメージ再ビルド
dc build --no-cache

# 起動
dc up -d
```

---

## よく使うコマンド

```bash
# コンテナ起動
dc up -d

# コンテナ停止
dc down

# ログ確認
dc logs -f django

# Djangoシェル
dj shell

# マイグレーション作成
dj makemigrations

# テスト実行
dj pytest
```

---

## 関連ドキュメント

- `docs/COMMANDS.md` - よく使うコマンド一覧
- `docs/PROJECT_INFO.md` - プロジェクト情報
- `docs-private/aws/` - AWS環境設計書

---

**作成日**: 2025-10-23
**作成者**: AI（Claude Code）+ hirok
**バージョン**: 1.0

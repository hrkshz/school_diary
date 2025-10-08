# 連絡帳管理システム

中学校向け生徒・担任間連絡管理システム。生徒が日々の振り返りを記録し、担任が確認・フィードバックを行うWebアプリケーション。

## 技術スタック

- **Backend**: Python 3.12 / Django 5.1
- **Database**: PostgreSQL 16
- **Cache/Queue**: Redis 7
- **Task Queue**: Celery 5.4
- **Infrastructure**: Docker / Docker Compose
- **Admin UI**: django-jazzmin
- **Forms**: django-crispy-forms (Bootstrap 5)

## 主要機能

### 生徒向け機能
- 連絡帳の作成・提出
- 体調・メンタル状態の記録
- 過去の連絡帳閲覧

### 担任向け機能
- 連絡帳の確認・既読管理
- 担任メモの作成・共有
- クラス単位での一覧表示

### 管理者機能
- ユーザー・クラス管理
- データの一括管理
- 検索・フィルタ機能

## セットアップ

### 前提条件
- Docker Desktop インストール済み
- Git インストール済み

### 環境構築手順

```bash
# 1. リポジトリクローン
git clone [repository-url]
cd school_diary

# 2. 環境変数設定
cp .envs/.local/.django.example .envs/.local/.django
cp .envs/.local/.postgres.example .envs/.local/.postgres

# 3. Docker環境起動
docker compose -f docker-compose.local.yml build
docker compose -f docker-compose.local.yml up -d

# 4. マイグレーション実行
docker compose -f docker-compose.local.yml run --rm django python manage.py migrate

# 5. テストユーザー・データ作成
docker compose -f docker-compose.local.yml run --rm django python manage.py create_test_users
docker compose -f docker-compose.local.yml run --rm django python manage.py create_sample_diaries
```

### アクセスURL
- **開発サーバー**: http://localhost:8000
- **管理画面**: http://localhost:8000/admin
- **Mailpit（メール確認）**: http://localhost:8025

## テストアカウント

### 管理者
- メールアドレス: `admin@example.com`
- パスワード: `admin123`

### 担任
- メールアドレス: `teacher_1_A@example.com` ～ `teacher_3_B@example.com`（6名）
- パスワード: `password123`
- 担当クラス: 1年A組 ～ 3年B組

### 生徒
- メールアドレス: `student_001@example.com` ～ `student_030@example.com`（30名）
- パスワード: `password123`
- 各クラス5名ずつ配置済み

## ドキュメント

プロジェクトの設計・仕様に関するドキュメントは `docs/` ディレクトリに格納されています。

- [要件定義書](docs/要件定義書.md)
- [データモデル設計書](docs/データモデル設計書.md)
- [機能仕様書](docs/機能仕様書.md)
- [システムアーキテクチャ設計書](docs/システムアーキテクチャ設計書.md)
- [テスト計画書](docs/テスト計画書.md)

## 開発環境

本プロジェクトはClaude Code（AIペアプログラミングツール）を使用して開発されました。AIはコード生成補助、デバッグ支援を担当し、設計・実装・テストの最終判断は開発者が実施しています。

### インフラ構成

**開発環境**:
- Docker Compose による多コンテナ構成
- PostgreSQL 16、Redis 7、Celery ワーカー

**本番環境（予定）**:
- AWS（Amazon Web Services）
- Infrastructure as Code: Terraform
- 主要サービス: EC2/ECS、RDS（PostgreSQL）、ElastiCache（Redis）

### 使用コマンド

```bash
# Dockerコンテナ起動
docker compose -f docker-compose.local.yml up -d

# Djangoコマンド実行
docker compose -f docker-compose.local.yml run --rm django python manage.py [command]

# ログ確認
docker compose -f docker-compose.local.yml logs -f django

# 環境停止
docker compose -f docker-compose.local.yml down
```

## ライセンス

MIT

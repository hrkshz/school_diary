# 連絡帳管理システム - 技術仕様書

**バージョン**: v0.3.0-map
**作成日**: 2025-10-29
**対象読者**: IT担当者、システム運用担当者

---

## 📑 目次

- [1. システム構成](#1-システム構成)
- [2. 技術スタック](#2-技術スタック)
- [3. デプロイ情報](#3-デプロイ情報)
- [4. データモデル概要](#4-データモデル概要)
- [5. 監視・ログ](#5-監視ログ)
- [6. バックアップ・復旧](#6-バックアップ復旧)
- [7. セキュリティ](#7-セキュリティ)

---

## 1. システム構成

### アーキテクチャ図

```
インターネット
    ↓
CloudFront（CDN、HTTPS強制）
    ↓
Network Load Balancer（SSL終端、ヘルスチェック）
    ↓
EC2（Django + Gunicorn + Docker）
    ↓
RDS（PostgreSQL 16、プライベートサブネット）
```

### コンポーネント説明

| コンポーネント            | 役割                          | 理由                                                   |
| ------------------------- | ----------------------------- | ------------------------------------------------------ |
| **CloudFront**            | CDN、HTTPS 強制               | グローバルエッジロケーション、静的ファイル配信の高速化 |
| **Network Load Balancer** | L4 ロードバランサー、SSL 終端 | ヘルスチェック、スケーラビリティ                       |
| **EC2**                   | アプリケーション実行          | Docker コンテナ実行、スケーラブル                      |
| **RDS**                   | マネージド PostgreSQL         | 自動バックアップ、Multi-AZ 対応可能                    |

### ネットワーク構成

```
VPC (10.0.0.0/16)
├── パブリックサブネット (10.0.1.0/24)
│   ├── Network Load Balancer
│   └── NAT Gateway
└── プライベートサブネット (10.0.10.0/24)
    ├── EC2インスタンス
    └── RDS（PostgreSQL）
```

---

## 2. 技術スタック

### バックエンド

| 技術               | バージョン | 用途                       |
| ------------------ | ---------- | -------------------------- |
| **Python**         | 3.12       | プログラミング言語         |
| **Django**         | 5.1        | Web フレームワーク         |
| **PostgreSQL**     | 16         | リレーショナルデータベース |
| **Gunicorn**       | 22.0       | WSGI サーバー（本番環境）  |
| **django-allauth** | 0.57       | 認証・認可                 |

### フロントエンド

| 技術                 | バージョン | 用途                           |
| -------------------- | ---------- | ------------------------------ |
| **Bootstrap**        | 5.3        | CSS フレームワーク             |
| **Django Templates** | -          | サーバーサイドレンダリング     |
| **AJAX**             | -          | 既読処理、出席記録の非同期通信 |

### インフラ

| 技術               | バージョン | 用途                  |
| ------------------ | ---------- | --------------------- |
| **Docker**         | 27.x       | コンテナ化            |
| **Docker Compose** | 2.x        | 開発環境              |
| **Terraform**      | 1.5+       | IaC（インフラ自動化） |
| **AWS**            | -          | クラウドインフラ      |

### 開発ツール

| 技術       | バージョン | 用途                 |
| ---------- | ---------- | -------------------- |
| **uv**     | 0.4+       | 依存関係管理         |
| **Ruff**   | 0.6+       | Linter / Formatter   |
| **pytest** | 8.x        | テストフレームワーク |
| **mypy**   | 1.11+      | 型チェック           |

---

## 3. デプロイ情報

### 本番環境 URL

- **アプリケーション**: https://d2wk3j2pacp33b.cloudfront.net
- **管理画面**: https://d2wk3j2pacp33b.cloudfront.net/admin/

### 環境変数

本番環境では以下の環境変数を設定してください。

**必須環境変数**:

| 変数名                   | 説明                | 例                                      |
| ------------------------ | ------------------- | --------------------------------------- |
| `DJANGO_SECRET_KEY`      | Django 秘密鍵       | ランダムな 64 文字                      |
| `DATABASE_URL`           | PostgreSQL 接続 URL | `postgres://user:pass@host:5432/dbname` |
| `DJANGO_ALLOWED_HOSTS`   | 許可ホスト          | `d2wk3j2pacp33b.cloudfront.net`         |
| `DJANGO_SETTINGS_MODULE` | Django 設定         | `config.settings.production`            |

**AWS 関連**:

| 変数名                    | 説明                 |
| ------------------------- | -------------------- |
| `AWS_ACCESS_KEY_ID`       | AWS アクセスキー     |
| `AWS_SECRET_ACCESS_KEY`   | AWS シークレットキー |
| `AWS_STORAGE_BUCKET_NAME` | S3 バケット名        |

### デプロイ手順（Terraform）

#### 前提条件

- AWS CLI インストール済み
- Terraform インストール済み（v1.5 以上）
- AWS クレデンシャル設定済み

#### 手順

```bash
# 1. AWSクレデンシャルの設定
export AWS_ACCESS_KEY_ID="<your-access-key>"
export AWS_SECRET_ACCESS_KEY="<your-secret-key>"
export AWS_DEFAULT_REGION="ap-northeast-1"

# 2. Terraformディレクトリに移動
cd terraform

# 3. Terraformの初期化
terraform init

# 4. デプロイ計画の確認
terraform plan

# 5. インフラの構築（約10分）
terraform apply

# 6. 出力情報の確認
terraform output
```

#### 期待される出力

```
cloudfront_domain = "d2wk3j2pacp33b.cloudfront.net"
ec2_public_ip = "54.xxx.xxx.xxx"
rds_endpoint = "school-diary.xxx.ap-northeast-1.rds.amazonaws.com"
```

### Docker Compose によるローカル開発環境

```bash
# 1. リポジトリのクローン
git clone <repository-url>
cd school_diary

# 2. 開発環境の起動
docker compose -f compose/local/docker-compose.yml up -d

# 3. マイグレーション実行
docker compose -f compose/local/docker-compose.yml exec django python manage.py migrate

# 4. テストデータ作成
docker compose -f compose/local/docker-compose.yml exec django python manage.py create_test_users

# 5. アクセス
# http://localhost:8000
```

---

## 4. データモデル概要

### 主要テーブル

| テーブル名          | 説明     | 主要フィールド                                                                                          |
| ------------------- | -------- | ------------------------------------------------------------------------------------------------------- |
| **User**            | ユーザー | email, password, role（生徒/担任/学年主任/校長/管理者）                                                 |
| **ClassRoom**       | クラス   | grade（学年）, class_name（A 組/B 組など）, year（年度）                                                |
| **DiaryEntry**      | 連絡帳   | date, health_condition（体調）, mental_state（メンタル）, reflection（振り返り）, is_read（既読フラグ） |
| **TeacherNote**     | 担任メモ | content, is_shared（学年共有フラグ）, created_by                                                        |
| **DailyAttendance** | 出席記録 | date, status（出席/欠席/遅刻/早退）, absence_reason                                                     |

### データベース設計の特徴

#### セキュリティ

- パスワードはハッシュ化（Django 標準の PBKDF2）
- SQL インジェクション対策（Django ORM による自動エスケープ）
- CSRF 対策（Django 標準機能）

#### パフォーマンス最適化

- N+1 問題対策（select_related/prefetch_related）
- インデックス設定（日付、学年、クラス）
- ページネーション（大量データの分割表示）

#### データ整合性

- 外部キー制約
- ユニーク制約（1 日 1 件の連絡帳）
- NOT NULL 制約（必須フィールド）

---

## 5. 監視・ログ

### CloudWatch 監視

以下のメトリクスを監視しています。

| メトリクス         | 閾値 | アラート条件         |
| ------------------ | ---- | -------------------- |
| **CPU 使用率**     | 80%  | 5 分間連続で超過     |
| **メモリ使用率**   | 80%  | 5 分間連続で超過     |
| **RDS 接続数**     | 80%  | 最大接続数の 80%超過 |
| **ディスク使用率** | 85%  | 85%超過              |

### ログ

| ログ種別                 | 保存先          | 保持期間 |
| ------------------------ | --------------- | -------- |
| **アプリケーションログ** | CloudWatch Logs | 30 日    |
| **エラーログ**           | CloudWatch Logs | 90 日    |
| **アクセスログ**         | CloudWatch Logs | 14 日    |

---

## 6. バックアップ・復旧

### RDS 自動バックアップ

- **バックアップ頻度**: 日次
- **保持期間**: 7 日間
- **バックアップウィンドウ**: 03:00-04:00（日本時間）

### 復旧手順

```bash
# 1. 特定時点へのリストア
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier school-diary-prod \
  --target-db-instance-identifier school-diary-restored \
  --restore-time 2025-10-28T12:00:00Z

# 2. DNSの切り替え（Terraformで管理）
terraform apply -var="rds_endpoint=<new-endpoint>"
```

---

## 7. セキュリティ

### 多層防御

| 層                     | 対策                                                         |
| ---------------------- | ------------------------------------------------------------ |
| **ネットワーク層**     | セキュリティグループ、NACL によるファイアウォール            |
| **アプリケーション層** | Django CSRF 保護、XSS 対策、SQL インジェクション対策         |
| **データ層**           | RDS プライベートサブネット配置、IAM ロールによるアクセス制御 |

---

**作成日**: 2025-10-29
**関連ドキュメント**: [操作マニュアル](MANUAL_FOR_CLIENT.md)

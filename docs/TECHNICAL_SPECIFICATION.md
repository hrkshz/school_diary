# 連絡帳管理システム - 技術仕様書

本書は、現在の実装と AWS/Terraform 構成に基づく技術仕様をまとめた文書です。  
公開デモの入口は [README.md](../README.md) を参照してください。

---

## 1. システム構成

### アーキテクチャ概要

```text
Internet
  ↓
CloudFront (HTTPS endpoint)
  ↓
Application Load Balancer
  ↓
EC2 (Docker / Django / Gunicorn)
  ↓
RDS PostgreSQL 16
```

### コンポーネント

| コンポーネント | 役割 |
| --- | --- |
| CloudFront | 公開エンドポイント、HTTPS 配信 |
| ALB | HTTP ルーティング、ヘルスチェック |
| EC2 | Django アプリケーション実行 |
| RDS | PostgreSQL データベース |
| S3 | 静的/メディアファイル保管 |
| ECR | Docker イメージ保管 |
| SES | メール送信 |
| CloudWatch | 監視・ログ |

### 注意

- Terraform の実体は **Application Load Balancer** です。
- URL は環境再構築時に変わる可能性があるため、本書には固定 CloudFront URL を直接持たせません。

---

## 2. アプリケーション構成

### バックエンド

| 技術 | バージョン | 用途 |
| --- | --- | --- |
| Python | 3.12 | 言語 |
| Django | 5.1 | Web フレームワーク |
| Gunicorn | 23.0 | WSGI サーバー |
| django-allauth | 65.x | 認証 |
| simple-history | 3.5.x | 変更履歴 |

### フロントエンド

| 技術 | 用途 |
| --- | --- |
| Bootstrap 5.3 | UI |
| Django Templates | SSR |
| AJAX | 非同期操作 |

### インフラ / 運用

| 技術 | 用途 |
| --- | --- |
| Docker / Docker Compose | ローカル・本番コンテナ実行 |
| Terraform | AWS インフラ構築 |
| Ruff / mypy / pytest | 品質管理 |

---

## 3. 主要環境変数

| 変数名 | 説明 | 例 |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Django 秘密鍵 | ランダム文字列 |
| `DATABASE_URL` | PostgreSQL 接続文字列 | `postgres://user:pass@host:5432/dbname` |
| `DJANGO_ALLOWED_HOSTS` | 許可ホスト | `<cloudfront-domain>` |
| `DJANGO_SITE_URL` | 外部公開 URL | `https://<cloudfront-domain>` |
| `DJANGO_SETTINGS_MODULE` | 設定モジュール | `config.settings.production` |
| `AWS_STORAGE_BUCKET_NAME` | S3 バケット名 | Terraform output 参照 |

公開デモ URL は [README.md](../README.md) を参照してください。

---

## 4. Terraform 出力と参照方法

本番環境構築後は以下を確認します。

```bash
cd terraform/environments/production
terraform output
```

主要 output:

- `cloudfront_domain_name`
- `alb_dns_name`
- `ec2_public_ip`
- `rds_endpoint`
- `s3_bucket_name`
- `ecr_repository_url`

CloudFront ドメインや現在の公開先の更新は、ポートフォリオ公開方針に合わせて [README.md](../README.md) のデモ導線を更新します。

---

## 5. ローカル開発

ローカル環境の詳細手順は [LOCAL_DEPLOYMENT.md](./LOCAL_DEPLOYMENT.md) を参照してください。  
現行のローカル起動ファイルは `docker-compose.local.yml` です。

基本コマンド:

```bash
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml exec django python manage.py migrate
docker compose -f docker-compose.local.yml exec django python manage.py create_test_data --diary-days 7 --students-per-class 10
```

---

## 6. データモデル概要

主要モデル:

- `User` / `UserProfile`
- `ClassRoom`
- `DiaryEntry`
- `TeacherNote`
- `TeacherNoteReadStatus`
- `DailyAttendance`

特徴:

- 1 生徒 1 日 1 件の連絡帳
- ロールベースアクセス制御
- 担任メモ共有と既読管理
- 出席記録と連絡帳を分離した設計

---

## 7. 監視・運用

監視対象:

- EC2 / ALB / RDS のメトリクス
- CloudWatch Logs
- Django health check: `/diary/health/`

現状:

- CloudWatch アラームは Terraform 管理で一部導入済み
- RDS automated backup は 7 日保持
- 運用強化の今後方針は [ITOM_ROADMAP.md](./ITOM_ROADMAP.md) を参照

将来拡張候補:

- EventBridge によるイベント集約
- Lambda によるイベント正規化
- Systems Manager OpsCenter / Automation
- AWS Backup restore testing
- AWS Config
- ServiceNow PDI 連携

補足:

- 再構築や公開先の切り替えにより URL が変わる可能性があります。
- ポートフォリオとして見せる公開デモの導線は [README.md](../README.md) に集約しています。

---

## 8. 参考ドキュメント

- [SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)
- [TERRAFORM_ARCHITECTURE.md](./TERRAFORM_ARCHITECTURE.md)
- [LOCAL_DEPLOYMENT.md](./LOCAL_DEPLOYMENT.md)
- [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)

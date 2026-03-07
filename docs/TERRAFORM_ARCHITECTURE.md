# Terraform インフラ構成

本書は、この制作物で現在採用している AWS/Terraform 構成をまとめた文書です。  
正本は Terraform 定義そのものであり、特に `terraform/environments/production/main.tf`、`terraform/modules/alb/main.tf`、`terraform/environments/production/outputs.tf` を基準にしています。

---

## 1. 構成の全体像

```text
User Browser
  ↓ HTTPS
CloudFront
  ↓ HTTP
Application Load Balancer
  ↓ HTTP:8000
EC2 (Docker / Django / Gunicorn)
  ↓ PostgreSQL
RDS PostgreSQL 16

Support Services:
- S3
- ECR
- SES
- CloudWatch / CloudWatch Logs
```

### 現在構成のポイント

- 公開入口は CloudFront
- アプリケーション入口は ALB
- Django アプリは EC2 上の Docker コンテナで実行
- データベースは RDS PostgreSQL
- 補助サービスとして S3、ECR、SES、CloudWatch を利用

---

## 2. Terraform の構成単位

`terraform/environments/production/main.tf` では、次のモジュールを組み合わせています。

| モジュール | 役割 |
| --- | --- |
| `vpc` | VPC、サブネット、ルートテーブル、S3 VPC Endpoint |
| `security_groups` | ALB、EC2、RDS の通信制御 |
| `s3` | 静的/メディアファイル保管 |
| `iam` | EC2 に付与する AWS 権限 |
| `ecr` | Docker イメージ保管 |
| `rds` | PostgreSQL データベース |
| `ec2` | Django アプリケーションサーバー |
| `alb` | Application Load Balancer と Target Group |
| `cloudfront` | HTTPS 公開入口 |
| `ses` | メール送信 |
| `cloudwatch` | メトリクス監視、アラート |
| `cloudwatch_logs` | ログ集約 |

---

## 3. 通信経路

### Public Path

```text
Browser
  -> CloudFront
  -> ALB
  -> EC2:8000
```

### Data Path

```text
EC2
  -> RDS:5432
```

### 補助経路

- EC2 -> S3: 静的/メディアファイル操作
- EC2 -> SES: メール送信
- EC2 / ALB / RDS -> CloudWatch: 監視とログ
- ECR -> EC2: Docker イメージ取得

---

## 4. 主要リソース

### CloudFront

- HTTPS の公開エンドポイント
- オリジンは ALB
- URL は再構築時に変わる可能性があるため、ポートフォリオで見せる公開デモの導線は [README.md](../README.md) で管理

### ALB

- `terraform/modules/alb/main.tf` で `load_balancer_type = "application"`
- Public Subnet 2 系統に配置
- Target Group は EC2 の `8000` 番ポートへ転送
- ヘルスチェックは `/diary/health/`

### EC2

- Docker 上で Django / Gunicorn を実行
- ALB 経由のアプリ通信と、管理者 IP からの SSH を許可

### RDS

- PostgreSQL 16
- Private Subnet に配置
- EC2 Security Group からのみ接続可能

---

## 5. セキュリティ設計

### ネットワーク分離

- Public Subnet: ALB、EC2
- Private Subnet: RDS

### Security Group の流れ

```text
CloudFront
  -> ALB Security Group
  -> EC2 Security Group
  -> RDS Security Group
```

### 方針

- RDS はインターネット非公開
- EC2 のアプリポートは ALB からのみ許可
- SSH は管理者 IP のみに制限

---

## 6. Terraform outputs

本番環境確認でよく使う output は以下です。

- `cloudfront_domain_name`
- `alb_dns_name`
- `ec2_public_ip`
- `rds_endpoint`
- `s3_bucket_name`
- `ecr_repository_url`

確認コマンド:

```bash
cd terraform/environments/production
terraform output
```

公開デモ URL を更新する場合は、[README.md](../README.md) のデモ導線を更新します。

---

## 7. ドキュメントの読み分け

- 技術仕様全体を見たい: [TECHNICAL_SPECIFICATION.md](./TECHNICAL_SPECIFICATION.md)
- 公開デモの入口を確認したい: [README.md](../README.md)
- 実際の構築記録を見たい: [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)

---

## 8. 補足

- 現在の repo には GitLab CI/CD 定義は含まれていません。
- そのため、本書では現行インフラ構成のみを扱い、過去の運用手段は正本に含めません。

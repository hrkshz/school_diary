# Terraform インフラ構成

本書は、この制作物で現在採用している AWS/Terraform 構成をまとめた文書です。正本は Terraform 定義そのものであり、特に `terraform/environments/shared/main.tf`、`terraform/environments/app/main.tf`、`terraform/modules/alb/main.tf`、`terraform/environments/app/outputs.tf` を基準にしています。

---

## 1. 構成の全体像

```text
User Browser
  ↓ HTTPS
CloudFront
  ↓ active: ALB / maintenance: S3
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
- CloudFront は `shared` state に残し、`app destroy` 後も URL を維持する
- `service_mode = maintenance` では private S3 の maintenance page を返す
- Django アプリは EC2 上の Docker コンテナで実行する
- データベースは RDS PostgreSQL

## 2. Terraform の構成単位

| 環境 | 役割 |
| --- | --- |
| `backend-bootstrap` | Terraform remote state 用 S3 bucket を作成 |
| `shared` | CloudFront、maintenance S3、永続 SSM、共有システム値 |
| `app` | VPC、ALB、EC2、RDS、ECR、CloudWatch、動的 SSM |

## 3. 通信経路

### Active

```text
Browser
  -> CloudFront
  -> ALB
  -> EC2:8000
```

### Maintenance

```text
Browser
  -> CloudFront
  -> S3 (maintenance page)
```

### Data Path

```text
EC2
  -> RDS:5432
```

## 4. 主要リソース

### CloudFront

- HTTPS の公開エンドポイント
- `shared` 管理なので `app destroy` では消えない
- `service_mode = active` では ALB を、`maintenance` では S3 をオリジンに使う

### ALB

- `terraform/modules/alb/main.tf` で `load_balancer_type = "application"`
- Public Subnet 2 系統に配置
- Target Group は EC2 の `8000` 番ポートへ転送
- ヘルスチェックは `/diary/health/`

### EC2

- Docker 上で Django / Gunicorn を実行
- SSM から `.env` を再生成して起動する

### RDS

- PostgreSQL 16
- Private Subnet に配置
- EC2 Security Group からのみ接続可能

## 5. Terraform outputs

よく使う出力:

- `terraform/environments/shared`: `cloudfront_domain_name`
- `terraform/environments/app`: `alb_dns_name`, `ec2_public_ip`, `rds_endpoint`, `ecr_repository_url`

## 6. 補足

- `shared` を maintenance に切り替えてから `app destroy` するのが通常運用
- `cloudfront.net` を維持したい間は CloudFront を `shared` から destroy しない
- 将来的に独自ドメインを使う場合は Route 53 + ACM を `shared` に追加する

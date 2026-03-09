#!/bin/bash
# Terraform output から .envs/.production/ の環境変数を自動生成する
#
# 使い方:
#   cd terraform/environments/production
#   terraform output -json > /tmp/tf-output.json
#   cd ../../..
#   bash scripts/generate-env.sh /tmp/tf-output.json
#
# 前提:
#   - terraform output -json の結果ファイルをパスで渡す
#   - jq がインストール済み
#   - DJANGO_SECRET_KEY と DB_PASSWORD は terraform.tfvars から取得

set -euo pipefail

TF_OUTPUT="${1:-}"
TF_DIR="terraform/environments/production"
ENV_DIR=".envs/.production"

if [ -z "$TF_OUTPUT" ]; then
  echo "Terraform output を取得します..."
  TF_OUTPUT=$(mktemp)
  (cd "$TF_DIR" && terraform output -json) > "$TF_OUTPUT"
fi

if ! command -v jq &> /dev/null; then
  echo "ERROR: jq が必要です。 sudo apt install jq"
  exit 1
fi

# Terraform output から値を取得
EC2_IP=$(jq -r '.ec2_public_ip.value' "$TF_OUTPUT")
ALB_DNS=$(jq -r '.alb_dns_name.value' "$TF_OUTPUT")
CF_DOMAIN=$(jq -r '.cloudfront_domain_name.value' "$TF_OUTPUT")
RDS_ENDPOINT=$(jq -r '.rds_endpoint.value' "$TF_OUTPUT")
S3_BUCKET=$(jq -r '.s3_bucket_name.value' "$TF_OUTPUT")
RDS_DB=$(jq -r '.rds_db_name.value' "$TF_OUTPUT")

# EC2 Instance ID は terraform output にないので AWS CLI で取得
EC2_INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=school-diary-production-ec2" "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].InstanceId" \
  --output text 2>/dev/null || echo "UNKNOWN")

# terraform.tfvars から DB パスワードを取得
DB_PASSWORD=$(grep 'db_password' "$TF_DIR/terraform.tfvars" | sed 's/.*= *"\(.*\)"/\1/')
DB_USERNAME=$(grep 'db_username' "$TF_DIR/terraform.tfvars" | sed 's/.*= *"\(.*\)"/\1/')

# 既存の DJANGO_SECRET_KEY を保持（あれば）
if [ -f "$ENV_DIR/.django" ]; then
  EXISTING_SECRET=$(grep 'DJANGO_SECRET_KEY' "$ENV_DIR/.django" | cut -d= -f2 || echo "")
else
  EXISTING_SECRET=""
fi

# SECRET_KEY がなければ生成
if [ -z "$EXISTING_SECRET" ]; then
  EXISTING_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")
fi

# RDS エンドポイントからホストを抽出（ポート除去）
RDS_HOST=$(echo "$RDS_ENDPOINT" | sed 's/:5432$//')

mkdir -p "$ENV_DIR"

# .django ファイル生成
cat > "$ENV_DIR/.django" << ENVEOF
# General
# ------------------------------------------------------------------------------
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=${EXISTING_SECRET}
DJANGO_ADMIN_URL=admin/
DJANGO_ALLOWED_HOSTS=${EC2_IP},${ALB_DNS},${CF_DOMAIN}

# Security
# ------------------------------------------------------------------------------
DJANGO_SECURE_SSL_REDIRECT=False

# Email
# ------------------------------------------------------------------------------
DJANGO_DEFAULT_FROM_EMAIL=hiroki0107@gmail.com
DJANGO_SERVER_EMAIL=

# Database (RDS)
# ------------------------------------------------------------------------------
DATABASE_URL=postgres://${DB_USERNAME}:${DB_PASSWORD}@${RDS_HOST}:5432/${RDS_DB}

# AWS
# ------------------------------------------------------------------------------
DJANGO_AWS_ACCESS_KEY_ID=
DJANGO_AWS_SECRET_ACCESS_KEY=
DJANGO_AWS_STORAGE_BUCKET_NAME=${S3_BUCKET}
DJANGO_AWS_S3_REGION_NAME=ap-northeast-1
AWS_REGION=ap-northeast-1
AWS_DEFAULT_REGION=ap-northeast-1
AWS_SES_REGION=ap-northeast-1
EC2_INSTANCE_ID=${EC2_INSTANCE_ID}

# django-allauth
# ------------------------------------------------------------------------------
DJANGO_ACCOUNT_ALLOW_REGISTRATION=True

# Gunicorn
# ------------------------------------------------------------------------------
WEB_CONCURRENCY=4
ENVEOF

# .postgres ファイル生成
cat > "$ENV_DIR/.postgres" << ENVEOF
# PostgreSQL (RDS)
# ------------------------------------------------------------------------------
POSTGRES_HOST=${RDS_HOST}
POSTGRES_PORT=5432
POSTGRES_DB=${RDS_DB}
POSTGRES_USER=${DB_USERNAME}
POSTGRES_PASSWORD=${DB_PASSWORD}
ENVEOF

echo "環境変数ファイルを生成しました:"
echo "  $ENV_DIR/.django"
echo "  $ENV_DIR/.postgres"
echo ""
echo "主要値:"
echo "  EC2 IP:         $EC2_IP"
echo "  ALB DNS:        $ALB_DNS"
echo "  CloudFront:     $CF_DOMAIN"
echo "  RDS Host:       $RDS_HOST"
echo "  EC2 Instance:   $EC2_INSTANCE_ID"
echo "  S3 Bucket:      $S3_BUCKET"

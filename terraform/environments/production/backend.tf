# Terraform Backend Configuration

# Phase 1A: Local state（初回デプロイ）
# 初回terraform initはlocal stateで実行
# 成功後、Phase 1BでS3 backendに移行

# Phase 1B以降: S3 backend（コメント解除して使用）
# terraform {
#   backend "s3" {
#     bucket = "school-diary-terraform-state"
#     key    = "production/terraform.tfstate"
#     region = "ap-northeast-1"
#   }
# }

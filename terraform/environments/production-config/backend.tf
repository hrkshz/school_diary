# Terraform Backend Configuration

# Phase 1A: Local state（初回構築）
# 初回 terraform init は local state で実行
# 必要に応じて後から S3 backend に移行

# terraform {
#   backend "s3" {
#     bucket = "school-diary-terraform-state"
#     key    = "production-config/terraform.tfstate"
#     region = "ap-northeast-1"
#   }
# }

# ECRリポジトリのURL（後で使用）
output "repository_url" {
  description = "ECRリポジトリのURL"
  value       = aws_ecr_repository.django.repository_url
  # 例: 123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/school-diary-production-django
}

output "repository_name" {
  description = "ECRリポジトリ名"
  value       = aws_ecr_repository.django.name
  # 例: school-diary-production-django
}

# 📚 学習ポイント:
# - outputは他のTerraformモジュールや外部で使用する値を出力
# - repository_urlはdocker pushするときに使用

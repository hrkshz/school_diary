# ECRリポジトリを作成
resource "aws_ecr_repository" "django" {
  # リポジトリ名: school-diary-production-django
  name = "${var.project_name}-${var.environment}-django"

  # イメージタグの変更を許可（latest, v1.0.0など）
  image_tag_mutability = "MUTABLE"

  # イメージをpushしたときに自動でセキュリティスキャン
  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-ecr"
    Environment = var.environment
  }
}

# イメージの自動削除ルール（コスト削減）
resource "aws_ecr_lifecycle_policy" "django_policy" {
  repository = aws_ecr_repository.django.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "最新10イメージのみ保持、それ以外は削除"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}

# - aws_ecr_repository: ECRリポジトリを作成するTerraformリソース
# - image_tag_mutability: MUTABLEは同じタグを上書き可能
# - scan_on_push: 脆弱性スキャンを自動実行（セキュリティ向上）

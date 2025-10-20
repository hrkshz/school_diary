# Data source for current AWS account ID
data "aws_caller_identity" "current" {}

# IAM Role for EC2 Instance
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-${var.environment}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-ec2-role"
    Environment = var.environment
  }
}

# S3 Access Policy (Specific bucket only)
resource "aws_iam_role_policy" "s3_policy" {
  name = "${var.project_name}-${var.environment}-s3-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ]
      Resource = [
        var.s3_bucket_arn,
        "${var.s3_bucket_arn}/*"
      ]
    }]
  })
}

# SES Policy (Email sending)
resource "aws_iam_role_policy" "ses_policy" {
  name = "${var.project_name}-${var.environment}-ses-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ses:SendEmail",
        "ses:SendRawEmail"
      ]
      # SES does not support resource-level permissions, must use "*"
      # checkov:skip=CKV_AWS_111:SES requires wildcard resource
      Resource = "*"
    }]
  })
}

# CloudWatch Logs Policy (Logging)
resource "aws_iam_role_policy" "cloudwatch_policy" {
  name = "${var.project_name}-${var.environment}-cloudwatch-policy"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ]
      Resource = [
        "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/ec2/${var.project_name}-${var.environment}*"
      ]
    }]
  })
}

# ECR Read権限をEC2に付与
resource "aws_iam_role_policy_attachment" "ecr_read" {
  # どのIAM roleに権限を付与するか
  role = aws_iam_role.ec2_role.name

  # どの権限を付与するか（AWS管理ポリシー）
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# 📚 学習ポイント:
# - aws_iam_role_policy_attachment: 既存のIAM roleにポリシーを追加
# - AmazonEC2ContainerRegistryReadOnly: ECR pullのみ許可（pushは不可）
# - AWS管理ポリシー: AWSが提供する既製の権限セット

# EC2 Instance Profile
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-${var.environment}-ec2-profile"
  role = aws_iam_role.ec2_role.name

  tags = {
    Name        = "${var.project_name}-${var.environment}-ec2-profile"
    Environment = var.environment
  }
}

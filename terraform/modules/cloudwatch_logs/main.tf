# CloudWatch Log Group for Django (Docker logs)
resource "aws_cloudwatch_log_group" "django" {
  name              = "/aws/ec2/${var.project_name}/${var.environment}/django"
  retention_in_days = 7 # Free tier: 5GB total

  tags = {
    Name        = "${var.project_name}-${var.environment}-django-logs"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# CloudWatch Log Stream for Django
resource "aws_cloudwatch_log_stream" "django" {
  name           = "django-stream"
  log_group_name = aws_cloudwatch_log_group.django.name
}

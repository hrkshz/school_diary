output "django_log_group_name" {
  description = "CloudWatch Log Group name for Django"
  value       = aws_cloudwatch_log_group.django.name
}

output "django_log_group_arn" {
  description = "CloudWatch Log Group ARN for Django"
  value       = aws_cloudwatch_log_group.django.arn
}

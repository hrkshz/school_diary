output "sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarms"
  value       = aws_sns_topic.alarms.arn
}

output "alarm_names" {
  description = "List of CloudWatch alarm names"
  value = [
    aws_cloudwatch_metric_alarm.alb_5xx.alarm_name,
    aws_cloudwatch_metric_alarm.alb_unhealthy_host.alarm_name,
    aws_cloudwatch_metric_alarm.alb_response_time.alarm_name,
    aws_cloudwatch_metric_alarm.alb_elb_5xx.alarm_name,
    aws_cloudwatch_metric_alarm.ec2_cpu.alarm_name,
    aws_cloudwatch_metric_alarm.ec2_status_check.alarm_name,
    aws_cloudwatch_metric_alarm.rds_cpu.alarm_name,
    aws_cloudwatch_metric_alarm.rds_connections.alarm_name,
    aws_cloudwatch_metric_alarm.rds_storage.alarm_name,
    aws_cloudwatch_metric_alarm.rds_read_latency.alarm_name,
    aws_cloudwatch_metric_alarm.rds_freeable_memory.alarm_name,
  ]
}

output "dashboard_arns" {
  description = "List of CloudWatch dashboard ARNs"
  value = [
    aws_cloudwatch_dashboard.availability.dashboard_arn,
    aws_cloudwatch_dashboard.db_health.dashboard_arn,
    aws_cloudwatch_dashboard.error_trends.dashboard_arn,
  ]
}

output "event_rule_arn" {
  description = "ARN of the alarm state change EventBridge rule"
  value       = aws_cloudwatch_event_rule.alarm_state_change.arn
}

# ============================================================================
# EventBridge: CloudWatch Alarm State Change
# ============================================================================

# CloudWatch Alarm の状態変化をキャプチャするルール
resource "aws_cloudwatch_event_rule" "alarm_state_change" {
  name        = "${var.project_name}-${var.environment}-alarm-state-change"
  description = "Capture CloudWatch Alarm state changes for project alarms"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
    detail = {
      state = {
        value = ["ALARM"]
      }
      alarmName = [{
        prefix = "${var.project_name}-${var.environment}"
      }]
    }
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-alarm-state-change"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# EventBridge Target: 既存 SNS トピックへ転送
resource "aws_cloudwatch_event_target" "alarm_to_sns" {
  rule      = aws_cloudwatch_event_rule.alarm_state_change.name
  target_id = "send-to-sns"
  arn       = var.sns_topic_arn
}

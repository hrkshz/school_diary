# SNS Topic for CloudWatch Alarms
resource "aws_sns_topic" "alarms" {
  name = "${var.project_name}-${var.environment}-cloudwatch-alarms"

  tags = {
    Name        = "${var.project_name}-${var.environment}-alarms"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# SNS Topic Subscription (Email)
resource "aws_sns_topic_subscription" "alarms_email" {
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# ============================================================================
# ALB Alarms (3)
# ============================================================================

# ALB: 5xx Errors
resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60 # 1 minute
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "[P2] Alert when ALB target returns more than 10 5xx errors in 1 minute"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "notBreaching" # データ欠損時はアラーム発動しない

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb-5xx"
    Environment = var.environment
    Severity    = "P2"
  }
}

# ALB: Unhealthy Host Count
resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_host" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-unhealthy-host"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Maximum"
  threshold           = 1
  alarm_description   = "[P1] Alert when any target is unhealthy"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
    TargetGroup  = var.alb_target_group_arn_suffix
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb-unhealthy"
    Environment = var.environment
    Severity    = "P1"
  }
}

# ALB: High Response Time
resource "aws_cloudwatch_metric_alarm" "alb_response_time" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = 300 # 5 minutes
  statistic           = "Average"
  threshold           = 3.0 # 3 seconds
  alarm_description   = "[P2] Alert when average response time exceeds 3 seconds"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb-response-time"
    Environment = var.environment
    Severity    = "P2"
  }
}

# ============================================================================
# EC2 Alarms (2)
# ============================================================================

# EC2: High CPU Utilization
resource "aws_cloudwatch_metric_alarm" "ec2_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-ec2-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300 # 5 minutes
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "[P3] Alert when EC2 CPU exceeds 80% for 5 minutes"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    InstanceId = var.ec2_instance_id
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-ec2-cpu"
    Environment = var.environment
    Severity    = "P3"
  }
}

# EC2: Status Check Failed
resource "aws_cloudwatch_metric_alarm" "ec2_status_check" {
  alarm_name          = "${var.project_name}-${var.environment}-ec2-status-check-failed"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = 60
  statistic           = "Maximum"
  threshold           = 1
  alarm_description   = "[P1] Alert when EC2 status check fails"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    InstanceId = var.ec2_instance_id
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-ec2-status-check"
    Environment = var.environment
    Severity    = "P1"
  }
}

# ============================================================================
# RDS Alarms (4)
# ============================================================================

# RDS: High CPU Utilization
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300 # 5 minutes
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "[P3] Alert when RDS CPU exceeds 80% for 5 minutes"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-cpu"
    Environment = var.environment
    Severity    = "P3"
  }
}

# RDS: High Database Connections
resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-connections-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "[P3] Alert when RDS connections exceed 80 (db.t3.micro: max_connections formula DBInstanceClassMemory/9531392)"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-connections"
    Environment = var.environment
    Severity    = "P3"
  }
}

# RDS: Low Free Storage Space
resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-storage-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 2147483648 # 2GB in bytes
  alarm_description   = "[P3] Alert when RDS free storage space is less than 2GB"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-storage"
    Environment = var.environment
    Severity    = "P3"
  }
}

# RDS: High Read Latency
resource "aws_cloudwatch_metric_alarm" "rds_read_latency" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-read-latency-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ReadLatency"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 0.1 # 100ms in seconds
  alarm_description   = "[P2] Alert when RDS read latency exceeds 100ms"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-read-latency"
    Environment = var.environment
    Severity    = "P2"
  }
}

# ============================================================================
# ALB Alarms (追加)
# ============================================================================

# ALB: ELB-level 5xx Errors (ALB自体のエラー)
resource "aws_cloudwatch_metric_alarm" "alb_elb_5xx" {
  alarm_name          = "${var.project_name}-${var.environment}-alb-elb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_ELB_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "[P2] Alert when ALB itself returns more than 5 5xx errors in 1 minute"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    LoadBalancer = var.alb_arn_suffix
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-alb-elb-5xx"
    Environment = var.environment
    Severity    = "P2"
  }
}

# ============================================================================
# RDS Alarms (追加)
# ============================================================================

# RDS: Low Freeable Memory
resource "aws_cloudwatch_metric_alarm" "rds_freeable_memory" {
  alarm_name          = "${var.project_name}-${var.environment}-rds-freeable-memory-low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FreeableMemory"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 128000000 # 128MB in bytes (t3.micro has ~1GB)
  alarm_description   = "[P3] Alert when RDS freeable memory falls below 128MB"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-freeable-memory"
    Environment = var.environment
    Severity    = "P3"
  }
}

# ============================================================================
# SNS Topic Policy
# ============================================================================

# CloudWatch Alarms と EventBridge からの Publish を許可
resource "aws_sns_topic_policy" "alarms" {
  arn = aws_sns_topic.alarms.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "AllowAlarmAndEventBridgePublish"
    Statement = [
      {
        Sid       = "AllowCloudWatchAlarms"
        Effect    = "Allow"
        Principal = { Service = "cloudwatch.amazonaws.com" }
        Action    = "sns:Publish"
        Resource  = aws_sns_topic.alarms.arn
      },
      {
        Sid       = "AllowEventBridge"
        Effect    = "Allow"
        Principal = { Service = "events.amazonaws.com" }
        Action    = "sns:Publish"
        Resource  = aws_sns_topic.alarms.arn
      }
    ]
  })
}

# ============================================================================
# CloudWatch Dashboards
# ============================================================================

# Availability Dashboard
resource "aws_cloudwatch_dashboard" "availability" {
  dashboard_name = "${var.project_name}-${var.environment}-availability"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "ALB Host Health"
          region = "ap-northeast-1"
          metrics = [
            ["AWS/ApplicationELB", "HealthyHostCount", "TargetGroup", var.alb_target_group_arn_suffix, "LoadBalancer", var.alb_arn_suffix, { stat = "Average", label = "Healthy Hosts" }],
            ["AWS/ApplicationELB", "UnHealthyHostCount", "TargetGroup", var.alb_target_group_arn_suffix, "LoadBalancer", var.alb_arn_suffix, { stat = "Average", label = "Unhealthy Hosts" }]
          ]
          period = 60
          view   = "timeSeries"
          stacked = true
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 6
        height = 6
        properties = {
          title  = "EC2 Status Check"
          region = "ap-northeast-1"
          metrics = [
            ["AWS/EC2", "StatusCheckFailed", "InstanceId", var.ec2_instance_id, { stat = "Maximum", label = "Status Check Failed" }]
          ]
          period = 60
          view   = "singleValue"
        }
      },
      {
        type   = "metric"
        x      = 18
        y      = 0
        width  = 6
        height = 6
        properties = {
          title  = "ALB Request Count"
          region = "ap-northeast-1"
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.alb_arn_suffix, { stat = "Sum", label = "Requests" }]
          ]
          period = 300
          view   = "timeSeries"
        }
      }
    ]
  })
}

# DB Health Dashboard
resource "aws_cloudwatch_dashboard" "db_health" {
  dashboard_name = "${var.project_name}-${var.environment}-db-health"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "RDS CPU Utilization"
          region = "ap-northeast-1"
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.rds_instance_id, { stat = "Average", label = "CPU %" }]
          ]
          period = 300
          view   = "timeSeries"
          yAxis = {
            left = { min = 0, max = 100, label = "%" }
          }
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "RDS Database Connections"
          region = "ap-northeast-1"
          metrics = [
            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", var.rds_instance_id, { stat = "Average", label = "Connections" }]
          ]
          period = 300
          view   = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "RDS Free Storage Space"
          region = "ap-northeast-1"
          metrics = [
            ["AWS/RDS", "FreeStorageSpace", "DBInstanceIdentifier", var.rds_instance_id, { stat = "Average", label = "Free Storage (bytes)" }]
          ]
          period = 300
          view   = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "RDS Freeable Memory"
          region = "ap-northeast-1"
          metrics = [
            ["AWS/RDS", "FreeableMemory", "DBInstanceIdentifier", var.rds_instance_id, { stat = "Average", label = "Freeable Memory (bytes)" }]
          ]
          period = 300
          view   = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "RDS Read Latency"
          region = "ap-northeast-1"
          metrics = [
            ["AWS/RDS", "ReadLatency", "DBInstanceIdentifier", var.rds_instance_id, { stat = "Average", label = "Read Latency (seconds)" }]
          ]
          period = 300
          view   = "timeSeries"
        }
      }
    ]
  })
}

# Error Trends Dashboard
resource "aws_cloudwatch_dashboard" "error_trends" {
  dashboard_name = "${var.project_name}-${var.environment}-error-trends"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 8
        height = 6
        properties = {
          title  = "Target 5XX Errors"
          region = "ap-northeast-1"
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", var.alb_arn_suffix, { stat = "Sum", label = "Target 5XX" }]
          ]
          period = 300
          view   = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 0
        width  = 8
        height = 6
        properties = {
          title  = "ELB 5XX Errors"
          region = "ap-northeast-1"
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", "LoadBalancer", var.alb_arn_suffix, { stat = "Sum", label = "ELB 5XX" }]
          ]
          period = 300
          view   = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 0
        width  = 8
        height = 6
        properties = {
          title  = "Target 4XX Errors"
          region = "ap-northeast-1"
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", "LoadBalancer", var.alb_arn_suffix, { stat = "Sum", label = "Target 4XX" }]
          ]
          period = 300
          view   = "timeSeries"
        }
      }
    ]
  })
}

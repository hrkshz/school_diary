variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "alarm_email" {
  description = "Email address to receive CloudWatch alarms"
  type        = string
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix for CloudWatch metrics (e.g., app/my-alb/1234567890abcdef)"
  type        = string
}

variable "alb_target_group_arn_suffix" {
  description = "ALB Target Group ARN suffix for CloudWatch metrics"
  type        = string
}

variable "ec2_instance_id" {
  description = "EC2 instance ID to monitor"
  type        = string
}

variable "rds_instance_id" {
  description = "RDS instance identifier to monitor"
  type        = string
}

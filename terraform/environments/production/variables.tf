variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "school-diary"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "public_subnet_cidr_2" {
  description = "CIDR block for public subnet 2 (for ALB Multi-AZ)"
  type        = string
  default     = "10.0.4.0/24"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "EC2 key pair name for SSH access"
  type        = string
}

variable "admin_ip" {
  description = "Admin IP address for SSH access (CIDR notation)"
  type        = string
  default     = "0.0.0.0/0"
}

# VPC - Private Subnet
variable "private_subnet_cidr" {
  description = "CIDR block for private subnet (RDS)"
  type        = string
  default     = "10.0.2.0/24"
}

variable "private_subnet_cidr_2" {
  description = "CIDR block for private subnet 2 (RDS Multi-AZ)"
  type        = string
  default     = "10.0.3.0/24"
}

# RDS Variables
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "school_diary"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "postgres"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "16.10"
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

variable "db_backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

# S3 Variables
variable "s3_bucket_name" {
  description = "S3 bucket name for static and media files (must be globally unique)"
  type        = string
}

variable "s3_versioning_enabled" {
  description = "Enable S3 bucket versioning"
  type        = bool
  default     = true
}

# SES Variables
variable "ses_sender_email" {
  description = "Email address to verify for SES (sender)"
  type        = string
  default     = "hiroki0107@gmail.com"
}

# GitHub Actions
variable "github_repo" {
  description = "GitHub repository (owner/repo format)"
  type        = string
  default     = "hrkshz/school_diary"
}

variable "github_bootstrap_ref" {
  description = "Git ref used by EC2 bootstrap to fetch deployment files from GitHub"
  type        = string
  default     = "main"
}

# CloudWatch Variables
variable "cloudwatch_alarm_email" {
  description = "Email address to receive CloudWatch alarms"
  type        = string
  default     = "hiroki0107@gmail.com"
}

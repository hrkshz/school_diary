variable "aws_region" {
  description = "AWS region for the Terraform backend bucket"
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

variable "backend_bucket_name" {
  description = "S3 bucket name for Terraform remote state"
  type        = string
}

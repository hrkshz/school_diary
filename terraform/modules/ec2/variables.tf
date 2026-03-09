variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "subnet_id" {
  description = "ID of the subnet for EC2 instance"
  type        = string
}

variable "security_group_id" {
  description = "ID of the security group for EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "key_name" {
  description = "EC2 key pair name for SSH access"
  type        = string
}

variable "iam_instance_profile" {
  description = "IAM instance profile name to attach to EC2"
  type        = string
  default     = ""
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository used for bootstrap"
  type        = string
}

variable "github_bootstrap_ref" {
  description = "Git ref used for bootstrap file download"
  type        = string
}

variable "parameter_prefix" {
  description = "SSM Parameter Store prefix for application configuration"
  type        = string
}

variable "ecr_repository_url" {
  description = "ECR repository URL used by bootstrap deployment"
  type        = string
}

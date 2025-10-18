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

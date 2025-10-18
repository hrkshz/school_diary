variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "subnet_id" {
  description = "ID of the subnet for NLB"
  type        = string
}

variable "ec2_instance_id" {
  description = "ID of the EC2 instance to be registered as target"
  type        = string
}

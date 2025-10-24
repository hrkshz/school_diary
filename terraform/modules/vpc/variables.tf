variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
}

variable "public_subnet_cidr" {
  description = "CIDR block for public subnet"
  type        = string
}

variable "public_subnet_cidr_2" {
  description = "CIDR block for public subnet 2 (for ALB Multi-AZ)"
  type        = string
}

variable "private_subnet_cidr" {
  description = "CIDR block for private subnet (for RDS)"
  type        = string
}

variable "private_subnet_cidr_2" {
  description = "CIDR block for private subnet 2 (for RDS Multi-AZ)"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "price_class" {
  description = "CloudFront distribution price class"
  type        = string
  default     = "PriceClass_200" # Japan, Asia, North America, Europe
}

variable "service_mode" {
  description = "CloudFront origin mode: active routes to ALB, maintenance routes to S3"
  type        = string
  default     = "active"

  validation {
    condition     = contains(["active", "maintenance"], var.service_mode)
    error_message = "service_mode must be either \"active\" or \"maintenance\"."
  }
}

variable "alb_dns_name" {
  description = "DNS name of the Application Load Balancer when service_mode is active"
  type        = string
  default     = null
  nullable    = true
}

variable "maintenance_bucket_name" {
  description = "S3 bucket name that stores the maintenance page"
  type        = string
}

variable "maintenance_bucket_arn" {
  description = "S3 bucket ARN that stores the maintenance page"
  type        = string
}

variable "maintenance_bucket_regional_domain_name" {
  description = "Regional domain name of the maintenance S3 bucket"
  type        = string
}

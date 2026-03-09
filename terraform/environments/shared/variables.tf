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

variable "service_mode" {
  description = "CloudFront routing mode"
  type        = string
  default     = "maintenance"

  validation {
    condition     = contains(["active", "maintenance"], var.service_mode)
    error_message = "service_mode must be either \"active\" or \"maintenance\"."
  }
}

variable "maintenance_bucket_name" {
  description = "S3 bucket name for the maintenance page"
  type        = string
}

variable "db_password" {
  description = "Persistent PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "django_secret_key" {
  description = "Persistent Django secret key"
  type        = string
  sensitive   = true
}

variable "django_settings_module" {
  description = "Django settings module"
  type        = string
  default     = "config.settings.production"
}

variable "django_admin_url" {
  description = "Admin URL path"
  type        = string
  default     = "admin/"
}

variable "django_secure_ssl_redirect" {
  description = "Whether to enable Django SECURE_SSL_REDIRECT"
  type        = bool
  default     = false
}

variable "django_account_allow_registration" {
  description = "Whether self registration is allowed"
  type        = bool
  default     = true
}

variable "django_default_from_email" {
  description = "Default from email address"
  type        = string
  default     = "hiroki0107@gmail.com"
}

variable "django_server_email" {
  description = "Server email address"
  type        = string
  default     = "hiroki0107@gmail.com"
}

variable "web_concurrency" {
  description = "Gunicorn worker count"
  type        = number
  default     = 4
}

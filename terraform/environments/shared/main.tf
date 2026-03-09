locals {
  parameter_prefix = "/${var.project_name}/${var.environment}"

  django_parameters = {
    DJANGO_SETTINGS_MODULE            = var.django_settings_module
    DJANGO_ADMIN_URL                  = var.django_admin_url
    DJANGO_SECURE_SSL_REDIRECT        = tostring(var.django_secure_ssl_redirect)
    DJANGO_DEFAULT_FROM_EMAIL         = var.django_default_from_email
    DJANGO_SERVER_EMAIL               = var.django_server_email
    DJANGO_ACCOUNT_ALLOW_REGISTRATION = tostring(var.django_account_allow_registration)
    WEB_CONCURRENCY                   = tostring(var.web_concurrency)
  }

  django_secure_parameters = {
    DJANGO_SECRET_KEY = var.django_secret_key
  }

  postgres_secure_parameters = {
    POSTGRES_PASSWORD = var.db_password
  }
}

module "maintenance_s3" {
  source = "../../modules/s3"

  project_name       = var.project_name
  environment        = "${var.environment}-shared"
  bucket_name        = var.maintenance_bucket_name
  versioning_enabled = true
}

resource "aws_s3_object" "maintenance_page" {
  bucket       = module.maintenance_s3.bucket_name
  key          = "index.html"
  source       = "${path.module}/../../files/maintenance.html"
  etag         = filemd5("${path.module}/../../files/maintenance.html")
  content_type = "text/html"
}

data "aws_ssm_parameter" "alb_dns_name" {
  count = var.service_mode == "active" ? 1 : 0

  name = "${local.parameter_prefix}/system/ALB_DNS_NAME"
}

module "cloudfront" {
  source = "../../modules/cloudfront"

  environment                             = var.environment
  service_mode                            = var.service_mode
  alb_dns_name                            = var.service_mode == "active" ? data.aws_ssm_parameter.alb_dns_name[0].value : null
  maintenance_bucket_name                 = module.maintenance_s3.bucket_name
  maintenance_bucket_arn                  = module.maintenance_s3.bucket_arn
  maintenance_bucket_regional_domain_name = module.maintenance_s3.bucket_regional_domain_name
}

resource "aws_ssm_parameter" "django_parameters" {
  for_each = local.django_parameters

  name  = "${local.parameter_prefix}/django/${each.key}"
  type  = "String"
  value = each.value

  tags = {
    Name        = "${var.project_name}-${var.environment}-django-${lower(each.key)}"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ssm_parameter" "django_secure_parameters" {
  for_each = local.django_secure_parameters

  name  = "${local.parameter_prefix}/django/${each.key}"
  type  = "SecureString"
  value = each.value

  tags = {
    Name        = "${var.project_name}-${var.environment}-django-${lower(each.key)}"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ssm_parameter" "postgres_secure_parameters" {
  for_each = local.postgres_secure_parameters

  name  = "${local.parameter_prefix}/postgres/${each.key}"
  type  = "SecureString"
  value = each.value

  tags = {
    Name        = "${var.project_name}-${var.environment}-postgres-${lower(each.key)}"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ssm_parameter" "shared_parameters" {
  for_each = {
    CLOUDFRONT_DOMAIN_NAME = module.cloudfront.cloudfront_domain_name
    SERVICE_MODE           = var.service_mode
  }

  name  = "${local.parameter_prefix}/system/${each.key}"
  type  = "String"
  value = each.value

  tags = {
    Name        = "${var.project_name}-${var.environment}-system-${lower(each.key)}"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

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

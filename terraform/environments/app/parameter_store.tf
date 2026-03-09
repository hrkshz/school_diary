locals {
  django_dynamic_parameters = {
    DJANGO_ALLOWED_HOSTS           = join(",", [module.alb.dns_name, data.aws_ssm_parameter.cloudfront_domain_name.value, module.ec2.private_ip])
    DJANGO_SITE_URL                = "https://${data.aws_ssm_parameter.cloudfront_domain_name.value}"
    DJANGO_AWS_STORAGE_BUCKET_NAME = module.s3.bucket_name
    DJANGO_AWS_S3_REGION_NAME      = var.aws_region
    AWS_REGION                     = var.aws_region
    AWS_DEFAULT_REGION             = var.aws_region
    AWS_SES_REGION                 = var.aws_region
  }

  postgres_parameters = {
    POSTGRES_HOST = split(":", module.rds.db_endpoint)[0]
    POSTGRES_PORT = tostring(module.rds.db_port)
    POSTGRES_DB   = module.rds.db_name
    POSTGRES_USER = var.db_username
  }

  system_parameters = {
    ALB_DNS_NAME = module.alb.dns_name
  }
}

data "aws_ssm_parameter" "db_password" {
  name            = "${local.parameter_prefix}/postgres/POSTGRES_PASSWORD"
  with_decryption = true
}

data "aws_ssm_parameter" "cloudfront_domain_name" {
  name = "${local.parameter_prefix}/system/CLOUDFRONT_DOMAIN_NAME"
}

resource "aws_ssm_parameter" "django_dynamic_parameters" {
  for_each = local.django_dynamic_parameters

  name  = "${local.parameter_prefix}/django/${each.key}"
  type  = "String"
  value = each.value

  tags = {
    Name        = "${var.project_name}-${var.environment}-django-${lower(each.key)}"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ssm_parameter" "postgres_parameters" {
  for_each = local.postgres_parameters

  name  = "${local.parameter_prefix}/postgres/${each.key}"
  type  = "String"
  value = each.value

  tags = {
    Name        = "${var.project_name}-${var.environment}-postgres-${lower(each.key)}"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ssm_parameter" "system_parameters" {
  for_each = local.system_parameters

  name  = "${local.parameter_prefix}/system/${each.key}"
  type  = "String"
  value = each.value

  tags = {
    Name        = "${var.project_name}-${var.environment}-system-${lower(each.key)}"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

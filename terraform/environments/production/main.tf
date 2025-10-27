module "vpc" {
  source = "../../modules/vpc"

  project_name           = var.project_name
  environment            = var.environment
  vpc_cidr               = var.vpc_cidr
  public_subnet_cidr     = var.public_subnet_cidr
  public_subnet_cidr_2   = var.public_subnet_cidr_2
  private_subnet_cidr    = var.private_subnet_cidr
  private_subnet_cidr_2  = var.private_subnet_cidr_2
}

module "security_groups" {
  source = "../../modules/security_groups"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.vpc.vpc_id
  admin_ip     = var.admin_ip
}

module "s3" {
  source = "../../modules/s3"

  project_name       = var.project_name
  environment        = var.environment
  bucket_name        = var.s3_bucket_name
  versioning_enabled = var.s3_versioning_enabled
}

module "iam" {
  source = "../../modules/iam"

  project_name  = var.project_name
  environment   = var.environment
  s3_bucket_arn = module.s3.bucket_arn
  aws_region    = var.aws_region
}

module "ecr" {
  source = "../../modules/ecr"

  project_name = var.project_name
  environment  = var.environment
}

module "rds" {
  source = "../../modules/rds"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.security_groups.rds_security_group_id]

  db_name                    = var.db_name
  db_username                = var.db_username
  db_password                = var.db_password
  db_instance_class          = var.db_instance_class
  db_allocated_storage       = var.db_allocated_storage
  db_engine_version          = var.db_engine_version
  db_multi_az                = var.db_multi_az
  db_backup_retention_period = var.db_backup_retention_period
}

module "ec2" {
  source = "../../modules/ec2"

  project_name         = var.project_name
  environment          = var.environment
  subnet_id            = module.vpc.public_subnet_id
  security_group_id    = module.security_groups.ec2_security_group_id
  instance_type        = var.instance_type
  key_name             = var.key_name
  iam_instance_profile = module.iam.instance_profile_name
}

module "alb" {
  source = "../../modules/alb"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc.vpc_id
  subnet_ids        = module.vpc.public_subnet_ids
  security_group_id = module.security_groups.alb_security_group_id
  ec2_instance_id   = module.ec2.instance_id
}

module "cloudfront" {
  source = "../../modules/cloudfront"

  alb_dns_name = module.alb.dns_name
  environment  = var.environment
}

module "ses" {
  source = "../../modules/ses"

  sender_email = var.ses_sender_email
  tags = {
    Name        = "${var.project_name}-${var.environment}-ses"
    Environment = var.environment
    Project     = var.project_name
  }
}

module "cloudwatch" {
  source = "../../modules/cloudwatch"

  project_name                  = var.project_name
  environment                   = var.environment
  alarm_email                   = var.cloudwatch_alarm_email
  alb_arn_suffix                = module.alb.alb_arn_suffix
  alb_target_group_arn_suffix   = module.alb.target_group_arn_suffix
  ec2_instance_id               = module.ec2.instance_id
  rds_instance_id               = module.rds.db_instance_identifier
}

module "cloudwatch_logs" {
  source = "../../modules/cloudwatch_logs"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
}

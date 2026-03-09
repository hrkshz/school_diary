output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.alb.dns_name
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = module.ec2.public_ip
}

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.rds.db_port
}

output "rds_db_name" {
  description = "Database name"
  value       = module.rds.db_name
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = module.s3.bucket_arn
}

output "iam_instance_profile_name" {
  description = "IAM instance profile name"
  value       = module.iam.instance_profile_name
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = module.ecr.repository_url
}

output "ecr_repository_name" {
  description = "ECR repository name"
  value       = module.ecr.repository_name
}

output "ses_email_identity_arn" {
  description = "SES email identity ARN"
  value       = module.ses.email_identity_arn
}

output "ses_verified_email" {
  description = "SES verified email address"
  value       = module.ses.email_address
}

output "eventbridge_rule_arn" {
  description = "EventBridge alarm state change rule ARN"
  value       = module.eventbridge.event_rule_arn
}

output "github_actions_role_arn" {
  description = "GitHub Actions IAM role ARN (for OIDC)"
  value       = module.github_actions.role_arn
}

output "parameter_store_prefix" {
  description = "SSM Parameter Store prefix for application configuration"
  value       = local.parameter_prefix
}

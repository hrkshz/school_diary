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

# ECR outputs
output "ecr_repository_url" {
  description = "ECRリポジトリのURL"
  value       = module.ecr.repository_url
}

output "ecr_repository_name" {
  description = "ECRリポジトリ名"
  value       = module.ecr.repository_name
}

# CloudFront outputs
output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name (HTTPS URL)"
  value       = module.cloudfront.cloudfront_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.cloudfront_distribution_id
}

# SES outputs
output "ses_email_identity_arn" {
  description = "SES email identity ARN"
  value       = module.ses.email_identity_arn
}

output "ses_verified_email" {
  description = "SES verified email address"
  value       = module.ses.email_address
}

# EventBridge outputs
output "eventbridge_rule_arn" {
  description = "EventBridge alarm state change rule ARN"
  value       = module.eventbridge.event_rule_arn
}

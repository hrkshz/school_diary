output "nlb_dns_name" {
  description = "DNS name of the Network Load Balancer"
  value       = module.nlb.dns_name
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

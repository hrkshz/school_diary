output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.cloudfront.cloudfront_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.cloudfront_distribution_id
}

output "maintenance_bucket_name" {
  description = "Maintenance page bucket name"
  value       = module.maintenance_s3.bucket_name
}

output "parameter_store_prefix" {
  description = "SSM Parameter Store prefix for shared configuration"
  value       = local.parameter_prefix
}

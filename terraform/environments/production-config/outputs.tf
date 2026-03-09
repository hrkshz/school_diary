output "parameter_store_prefix" {
  description = "SSM Parameter Store prefix for persistent application configuration"
  value       = local.parameter_prefix
}

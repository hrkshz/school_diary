output "dns_name" {
  description = "DNS name of the Network Load Balancer"
  value       = aws_lb.main.dns_name
}

output "arn" {
  description = "ARN of the Network Load Balancer"
  value       = aws_lb.main.arn
}

output "target_group_arn" {
  description = "ARN of the target group"
  value       = aws_lb_target_group.main.arn
}

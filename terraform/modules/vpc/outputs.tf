output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "ID of the public subnet"
  value       = aws_subnet.public.id
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = [aws_subnet.private.id, aws_subnet.private_2.id]
}

output "s3_vpc_endpoint_id" {
  description = "ID of the S3 VPC Endpoint"
  value       = aws_vpc_endpoint.s3.id
}

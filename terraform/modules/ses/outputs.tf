output "email_identity_arn" {
  description = "ARN of the SES email identity"
  value       = aws_ses_email_identity.sender.arn
}

output "email_address" {
  description = "Verified email address"
  value       = aws_ses_email_identity.sender.email
}

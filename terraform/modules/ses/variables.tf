variable "sender_email" {
  description = "Email address to verify for SES"
  type        = string
}

variable "tags" {
  description = "Tags to apply to SES resources"
  type        = map(string)
  default     = {}
}

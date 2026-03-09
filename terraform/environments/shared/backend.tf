# Terraform Backend Configuration
#
# Bootstrap once with terraform/environments/backend-bootstrap, then uncomment:
#
# terraform {
#   backend "s3" {
#     bucket       = "school-diary-terraform-state"
#     key          = "shared/terraform.tfstate"
#     region       = "ap-northeast-1"
#     use_lockfile = true
#   }
# }

# Get latest Ubuntu 24.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 Instance
resource "aws_instance" "main" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  key_name               = var.key_name
  iam_instance_profile   = var.iam_instance_profile != "" ? var.iam_instance_profile : null

  user_data = templatefile("${path.module}/../../files/user_data.sh.tftpl", {
    aws_region           = var.aws_region
    github_repository    = var.github_repo
    github_bootstrap_ref = var.github_bootstrap_ref
    parameter_prefix     = var.parameter_prefix
    ecr_repository_url   = var.ecr_repository_url
    ecr_registry         = split("/", var.ecr_repository_url)[0]
    ecr_repository_name  = split("/", var.ecr_repository_url)[1]
  })

  root_block_device {
    volume_size = 20
    volume_type = "gp2"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-ec2"
    Environment = var.environment
  }
}

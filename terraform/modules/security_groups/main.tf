# EC2 Security Group
resource "aws_security_group" "ec2" {
  name_prefix = "${var.project_name}-${var.environment}-ec2-"
  description = "Security group for EC2 instance"
  vpc_id      = var.vpc_id

  tags = {
    Name        = "${var.project_name}-${var.environment}-ec2-sg"
    Environment = var.environment
  }
}

# Allow SSH from admin IP only
resource "aws_security_group_rule" "ec2_ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = [var.admin_ip]
  security_group_id = aws_security_group.ec2.id
  description       = "Allow SSH from admin IP only"
}

# Allow HTTP on port 8000 from anywhere (NLB forwards traffic here)
resource "aws_security_group_rule" "ec2_http" {
  type              = "ingress"
  from_port         = 8000
  to_port           = 8000
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.ec2.id
  description       = "Allow HTTP on port 8000 from anywhere"
}

# Allow all outbound traffic
resource "aws_security_group_rule" "ec2_egress" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.ec2.id
  description       = "Allow all outbound traffic"
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-${var.environment}-rds-"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  tags = {
    Name        = "${var.project_name}-${var.environment}-rds-sg"
    Environment = var.environment
  }
}

# Allow PostgreSQL from EC2 only
resource "aws_security_group_rule" "rds_ingress" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.ec2.id
  security_group_id        = aws_security_group.rds.id
  description              = "Allow PostgreSQL from EC2"
}

# Network Load Balancer
resource "aws_lb" "main" {
  name               = "${var.project_name}-${var.environment}-nlb"
  internal           = false
  load_balancer_type = "network"
  subnets            = [var.subnet_id]

  enable_deletion_protection = false

  tags = {
    Name        = "${var.project_name}-${var.environment}-nlb"
    Environment = var.environment
  }
}

# Target Group
resource "aws_lb_target_group" "main" {
  name        = "${var.project_name}-${var.environment}-tg"
  port        = 8000
  protocol    = "TCP"
  vpc_id      = var.vpc_id
  target_type = "instance"

  health_check {
    enabled             = true
    interval            = 30
    port                = "traffic-port"
    protocol            = "TCP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-tg"
    Environment = var.environment
  }
}

# Target Group Attachment
resource "aws_lb_target_group_attachment" "main" {
  target_group_arn = aws_lb_target_group.main.arn
  target_id        = var.ec2_instance_id
  port             = 8000
}

# Listener
resource "aws_lb_listener" "main" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main.arn
  }
}

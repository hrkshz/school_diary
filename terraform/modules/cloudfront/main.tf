locals {
  active_origin_id      = "alb-origin"
  maintenance_origin_id = "maintenance-origin"
  target_origin_id      = var.service_mode == "active" ? local.active_origin_id : local.maintenance_origin_id
  allowed_methods       = var.service_mode == "active" ? ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"] : ["GET", "HEAD", "OPTIONS"]
}

resource "aws_cloudfront_origin_access_control" "maintenance" {
  name                              = "${var.environment}-maintenance-oac"
  description                       = "Origin access control for maintenance S3 bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.environment} - Django Application"
  price_class         = var.price_class
  wait_for_deployment = false
  default_root_object = var.service_mode == "maintenance" ? "index.html" : null

  dynamic "origin" {
    for_each = var.service_mode == "active" ? [1] : []

    content {
      domain_name = var.alb_dns_name
      origin_id   = local.active_origin_id

      custom_origin_config {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "http-only"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
  }

  origin {
    domain_name              = var.maintenance_bucket_regional_domain_name
    origin_id                = local.maintenance_origin_id
    origin_access_control_id = aws_cloudfront_origin_access_control.maintenance.id

    s3_origin_config {
      origin_access_identity = ""
    }
  }

  default_cache_behavior {
    allowed_methods  = local.allowed_methods
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = local.target_origin_id

    # AWS Managed Cache Policy: CachingDisabled
    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"

    # AWS Managed Origin Request Policy: AllViewer
    origin_request_policy_id = "216adef6-5c7f-47e4-b989-5492eafa07d3"

    viewer_protocol_policy = "redirect-to-https"
    compress               = true
  }

  dynamic "custom_error_response" {
    for_each = var.service_mode == "maintenance" ? [403, 404] : []

    content {
      error_code            = custom_error_response.value
      response_code         = 200
      response_page_path    = "/index.html"
      error_caching_min_ttl = 0
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name        = "${var.environment}-cloudfront"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

data "aws_iam_policy_document" "maintenance_bucket_access" {
  statement {
    sid    = "AllowCloudFrontReadMaintenancePage"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions = ["s3:GetObject"]
    resources = [
      "${var.maintenance_bucket_arn}/*",
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "maintenance" {
  bucket = var.maintenance_bucket_name
  policy = data.aws_iam_policy_document.maintenance_bucket_access.json
}

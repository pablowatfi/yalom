terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  default     = "yalom"
}

variable "pinecone_api_key" {
  description = "Pinecone API key"
  type        = string
  sensitive   = true
}

variable "groq_api_key" {
  description = "Groq API key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "s3_bucket_name" {
  description = "S3 bucket name for transcript backups"
  default     = "yalom-transcripts-backup"
}

variable "ui_bucket_name" {
  description = "S3 bucket name for static UI hosting"
  default     = "yalom-ui"
}

# DynamoDB table for ingestion state
resource "aws_dynamodb_table" "ingestion_state" {
  name         = "${var.project_name}-ingestion-state"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "record_id"
  range_key    = "source"

  attribute {
    name = "record_id"
    type = "S"
  }

  attribute {
    name = "source"
    type = "S"
  }

  tags = {
    Name = "Yalom Ingestion State"
  }
}

# S3 Bucket for transcript backups
resource "aws_s3_bucket" "transcripts" {
  bucket = var.s3_bucket_name

  tags = {
    Name        = "Yalom Transcripts"
    Environment = "production"
  }
}

# S3 Bucket for static UI
resource "aws_s3_bucket" "ui" {
  bucket = var.ui_bucket_name

  tags = {
    Name        = "Yalom UI"
    Environment = "production"
  }
}

resource "aws_s3_bucket_public_access_block" "ui" {
  bucket = aws_s3_bucket.ui.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "ui" {
  bucket = aws_s3_bucket.ui.id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

# CloudFront Origin Access Control (OAC)
resource "aws_cloudfront_origin_access_control" "ui" {
  name                              = "${var.project_name}-ui-oac"
  description                       = "OAC for Yalom UI"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_iam_policy_document" "ui_bucket_policy" {
  statement {
    actions = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.ui.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.ui.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "ui" {
  bucket = aws_s3_bucket.ui.id
  policy = data.aws_iam_policy_document.ui_bucket_policy.json
}

resource "aws_cloudfront_distribution" "ui" {
  enabled             = true
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.ui.bucket_regional_domain_name
    origin_id                = "${var.project_name}-ui-origin"
    origin_access_control_id = aws_cloudfront_origin_access_control.ui.id
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = "${var.project_name}-ui-origin"

    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
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

  price_class = "PriceClass_100"

  tags = {
    Name = "Yalom UI"
  }
}

resource "aws_s3_bucket_versioning" "transcripts_versioning" {
  bucket = aws_s3_bucket.transcripts.id

  versioning_configuration {
    status = "Enabled"
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# S3 access policy for Lambda
resource "aws_iam_role_policy" "lambda_s3_policy" {
  name = "${var.project_name}-lambda-s3-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.transcripts.arn,
          "${aws_s3_bucket.transcripts.arn}/*"
        ]
      }
    ]
  })
}

# DynamoDB access policy for Lambda
resource "aws_iam_role_policy" "lambda_dynamodb_policy" {
  name = "${var.project_name}-lambda-dynamodb-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem"
        ]
        Resource = [
          aws_dynamodb_table.ingestion_state.arn
        ]
      }
    ]
  })
}

# Lambda function for ingestion
resource "aws_lambda_function" "ingestion" {
  filename         = "${path.module}/../builds/ingestion.zip"
  function_name    = "${var.project_name}-ingestion"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../builds/ingestion.zip")
  runtime         = "python3.11"
  timeout         = 900
  memory_size     = 1024

  environment {
    variables = {
      PINECONE_API_KEY = var.pinecone_api_key
      S3_BUCKET        = aws_s3_bucket.transcripts.bucket
      OPENAI_API_KEY   = var.openai_api_key
      DDB_TABLE        = aws_dynamodb_table.ingestion_state.name
    }
  }

  tags = {
    Name = "Yalom Ingestion"
  }
}

# Lambda function for queries
resource "aws_lambda_function" "query" {
  filename         = "${path.module}/../builds/query.zip"
  function_name    = "${var.project_name}-query"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../builds/query.zip")
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 1024

  environment {
    variables = {
      PINECONE_API_KEY = var.pinecone_api_key
      GROQ_API_KEY     = var.groq_api_key
      OPENAI_API_KEY   = var.openai_api_key
    }
  }

  tags = {
    Name = "Yalom Query"
  }
}

# EventBridge rule for weekly ingestion
resource "aws_cloudwatch_event_rule" "weekly_ingestion" {
  name                = "${var.project_name}-weekly-ingestion"
  description         = "Weekly Huberman Lab transcript ingestion"
  schedule_expression = "cron(0 10 ? * MON *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.weekly_ingestion.name
  target_id = "IngestLambda"
  arn       = aws_lambda_function.ingestion.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekly_ingestion.arn
}

# API Gateway HTTP API
resource "aws_apigatewayv2_api" "query_api" {
  name          = "${var.project_name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "OPTIONS"]
    allow_headers = ["content-type"]
  }
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.query_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.query.invoke_arn
}

resource "aws_apigatewayv2_route" "query_route" {
  api_id    = aws_apigatewayv2_api.query_api.id
  route_key = "POST /query"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default_stage" {
  api_id      = aws_apigatewayv2_api.query_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.query.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.query_api.execution_arn}/*/*"
}

# Outputs
output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_api.query_api.api_endpoint
}

output "ingestion_lambda_arn" {
  description = "Ingestion Lambda ARN"
  value       = aws_lambda_function.ingestion.arn
}

output "query_lambda_arn" {
  description = "Query Lambda ARN"
  value       = aws_lambda_function.query.arn
}

output "s3_bucket_name" {
  description = "S3 bucket for transcripts"
  value       = aws_s3_bucket.transcripts.bucket
}

output "ui_bucket_name" {
  description = "S3 bucket for UI"
  value       = aws_s3_bucket.ui.bucket
}

output "ui_distribution_id" {
  description = "CloudFront distribution ID for UI"
  value       = aws_cloudfront_distribution.ui.id
}

output "ui_url" {
  description = "CloudFront URL for UI"
  value       = "https://${aws_cloudfront_distribution.ui.domain_name}"
}

# S3 Bucket for Source Data
resource "aws_s3_bucket" "source-data-bucket" {
  bucket        = "source-data-bucket-6i2caq"
  lifecycle {
    prevent_destroy = false
    ignore_changes = [force_destroy]
  }

  force_destroy = true
}

# S3 Bucket for processed data
resource "aws_s3_bucket" "target-data-bucket" {
  bucket        = "target-data-bucket-6i2caq"
  lifecycle {
    prevent_destroy = false
    ignore_changes = [force_destroy]
  }

  force_destroy = true
}

# S3 Bucket for saving code
resource "aws_s3_bucket" "code-bucket" {
  bucket        = "code-bucket-6i2caq"
  lifecycle {
    prevent_destroy = false
    ignore_changes = [force_destroy]
  }

  force_destroy = true
}

# s3 bucket for athnena results
resource "aws_s3_bucket" "athena_results" {
  bucket        = "athena-results-bucket-6i2caq"
  lifecycle {
    prevent_destroy = false
    ignore_changes = [force_destroy]
  }

  force_destroy = true
  tags = {
    Name = "AthenaResults"
  }
}

# Glue scripts
resource "aws_s3_object" "scripts" {
  for_each     = var.glue_scripts
  bucket       = aws_s3_bucket.code-bucket.id
  key          = "glue_scripts/${each.key}"
  source       = "${path.module}/${each.value}"
  etag         = filemd5("${path.module}/${each.value}")
  content_type = "text/x-python"
}

# Lambda function script
resource "aws_s3_object" "lambda_zip" {
  bucket = aws_s3_bucket.code-bucket.id
  key    = "lambda/lambda_function.zip"
  source = "${path.module}/lambda/lambda_function.zip"
  etag   = filemd5("${path.module}/lambda/lambda_function.zip")
}

# Lambda api function script
resource "aws_s3_object" "api_lambda_zip" {
  bucket = aws_s3_bucket.code-bucket.id
  key    = "lambda/api_lambda_function.zip"
  source = "${path.module}/lambda/api_lambda_function.zip"
  etag   = filemd5("${path.module}/lambda/api_lambda_function.zip")
}

# lambda layer
resource "aws_s3_object" "lambda_layer" {
  bucket = aws_s3_bucket.code-bucket.id
  key    = "lambda/lambda_layer.zip"
  source = "${path.module}/lambda/lambda_layer.zip"
  etag   = filemd5("${path.module}/lambda/lambda_layer.zip")
}

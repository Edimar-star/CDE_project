# IAM Role for Lambda
resource "aws_iam_role" "lambda_exec_role" {
  name = "lambda_exec_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Principal = {
        Service = "lambda.amazonaws.com"
      },
      Effect = "Allow"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_s3_write_access" {
  name = "lambda-s3-putobject"
  role = aws_iam_role.lambda_exec_role.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject"
        ],
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.target-data-bucket.id}",
          "arn:aws:s3:::${aws_s3_bucket.source-data-bucket.id}/raw/*",
          "arn:aws:s3:::${aws_s3_bucket.target-data-bucket.id}/model/*",
          "arn:aws:s3:::${aws_s3_bucket.target-data-bucket.id}/training/*"
        ]
      }
    ]
  })
}

resource "aws_s3_bucket_lifecycle_configuration" "temp_data_cleanup" {
  bucket = aws_s3_bucket.target-data-bucket.id

  rule {
    id     = "expire-temp-urls"
    status = "Enabled"

    filter {
      prefix = "temp/"
    }

    expiration {
      days = 1
    }
  }
}

# Lambda creation
resource "aws_lambda_function" "etl_lambda" {
  function_name     = "etl_lambda"
  role              = aws_iam_role.lambda_exec_role.arn
  handler           = "lambda_function.lambda_handler"
  runtime           = "python3.9"
  s3_bucket         = aws_s3_bucket.code-bucket.id
  s3_key            = aws_s3_object.lambda_zip.key
  source_code_hash  = filebase64sha256("${path.module}/lambda/lambda_function.zip")
  layers = [aws_lambda_layer_version.etl_layer.arn]

  memory_size   = 3008
  timeout       = 900 
}

# api lambda
resource "aws_lambda_function" "api_lambda" {
  function_name     = "api_lambda"
  role              = aws_iam_role.lambda_exec_role.arn
  handler           = "api_lambda_function.lambda_handler"
  runtime           = "python3.9"
  s3_bucket         = aws_s3_bucket.code-bucket.id
  s3_key            = aws_s3_object.api_lambda_zip.key
  source_code_hash  = filebase64sha256("${path.module}/lambda/api_lambda_function.zip")

  memory_size   = 3008
  timeout       = 900 
}

resource "aws_lambda_layer_version" "etl_layer" {
  s3_bucket           = aws_s3_bucket.code-bucket.id
  s3_key              = aws_s3_object.lambda_layer.key
  layer_name          = "etl_layer"
  compatible_runtimes = ["python3.9"]
}
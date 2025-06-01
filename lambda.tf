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

# Lambda creation
resource "aws_lambda_function" "etl_lambda" {
  function_name     = "etl_lambda"
  role              = aws_iam_role.lambda_exec_role.arn
  handler           = "lambda_function.lambda_handler"
  runtime           = "python3.9"
  s3_bucket         = aws_s3_bucket.code-bucket.id
  s3_key            = aws_s3_object.lambda_zip.key
  source_code_hash  = filebase64sha256("${path.module}/lambda/lambda_function.zip")
  layers = [
    "arn:aws:lambda:eu-central-1:770693421928:layer:Klayers-p39-numpy:5",
    "arn:aws:lambda:eu-central-1:770693421928:layer:Klayers-p39-pandas:9",
    "arn:aws:lambda:eu-central-1:770693421928:layer:Klayers-p39-scipy:4",
    "arn:aws:lambda:eu-central-1:770693421928:layer:Klayers-p39-netCDF4:1",
    aws_lambda_layer_version.etl_layer.arn
  ]
}

resource "aws_lambda_layer_version" "etl_layer" {
  s3_bucket           = aws_s3_bucket.code-bucket.id
  s3_key              = aws_s3_object.lambda_layer.key
  layer_name          = "etl_layer"
  compatible_runtimes = ["python3.9"]
}

# layer iam
resource "aws_iam_policy" "allow_get_layer_version_klayers" {
  name        = "AllowGetLayerVersionFromKlayers"
  description = "Permite lambda:GetLayerVersion en layers de Klayers"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = "lambda:GetLayerVersion",
        Resource = "arn:aws:lambda:eu-central-1:770693421928:layer:*"
      }
    ]
  })
}

resource "aws_iam_user_policy_attachment" "attach_get_layer_permission" {
  user       = "DEP_user"
  policy_arn = aws_iam_policy.allow_get_layer_version_klayers.arn
}
# Iam role
resource "aws_iam_role" "sagemaker_execution_role" {
  name = "sagemaker-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "sagemaker.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

# Iam policy
resource "aws_iam_role_policy_attachment" "sagemaker_policy" {
  role       = aws_iam_role.sagemaker_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# Model
resource "aws_sagemaker_model" "sklearn_model" {
  name                  = "fires-sklearn-model"
  execution_role_arn    = aws_iam_role.sagemaker_execution_role.arn

  primary_container {
    image               = "683313688378.dkr.ecr.${var.aws_region}.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
    model_data_url      = "s3://${aws_s3_bucket.target-data-bucket.id}/model/model.tar.gz"
  }
}

# Enpoint configuration
resource "aws_sagemaker_endpoint_configuration" "sklearn_endpoint_config" {
  name = "fires-sklearn-endpoint-config"

  production_variants {
    variant_name           = "AllTrafficVariant"
    model_name             = aws_sagemaker_model.sklearn_model.name
    initial_instance_count = 1
    instance_type          = "ml.m5.large"
  }
}

# Endpoint
resource "aws_sagemaker_endpoint" "sklearn_endpoint" {
  name = "fires-sklearn-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.sklearn_endpoint_config.name
}
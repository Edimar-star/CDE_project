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
    image               = "683313688378.dkr.ecr.eu-central-1.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
    model_data_url      = "s3://${aws_s3_bucket.target-data-bucket.id}/model/model.tar.gz"
  }
}
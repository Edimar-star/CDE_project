resource "aws_sagemaker_training_job" "sklearn_training" {
  name               = "fires-sklearn-training"
  role_arn           = aws_iam_role.sagemaker_execution_role.arn

  algorithm_specification {
    training_input_mode = "File"
    training_image      = "683313688378.dkr.ecr.${var.aws_region}.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
  }

  input_data_config {
    channel_name = "train"
    data_source {
      s3_data_source {
        s3_data_type               = "S3Prefix"
        s3_uri                     = "s3://${aws_s3_bucket.target-data-bucket.id}/training"
        s3_data_distribution_type = "FullyReplicated"
      }
    }
    content_type = "text/csv"
  }

  output_data_config {
    s3_output_path = "s3://${aws_s3_bucket.target-data-bucket.id}/model/"
  }

  resource_config {
    instance_type        = "ml.m5.large"
    instance_count       = 1
    volume_size_in_gb    = 10
  }

  stopping_condition {
    max_runtime_in_seconds = 900
  }

  enable_network_isolation = false
}

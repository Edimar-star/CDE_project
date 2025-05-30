resource "aws_glue_job" "glue_job" {
    name                = "glue-job"
    role_arn            = aws_iam_role.glue_service_role.arn
    description         = "Transform all tables and one table"
    glue_version        = "4.0"
    worker_type         = "G.1X"
    timeout             = 2880
    max_retries         = 1
    number_of_workers   = 1
    command {
      name              = "glueetl"
      python_version    = 3
      script_location   = "s3://${aws_s3_bucket.code-bucket.id}/glue_scripts/main.py"
    }
    default_arguments = {
      "--enable-auto-scaling"               = "true"
      "--enable-continuous-cloudwatch-log"  = "true"
      "--datalake-formats"                  = "delta"
      "--source-path"                       = "s3://${aws_s3_bucket.source-data-bucket.id}/"
      "--destination-path"                  = "s3://${aws_s3_bucket.target-data-bucket.id}/"
      "--job-name"                          = "glue-job"
      "--enable-continuous-log-filter"      = "true"
      "--enable-metrics"                    = "true"
    }
}

output "glue_crawler_name" {
  value = "s3://${aws_s3_bucket.source-data-bucket.id}/"
}
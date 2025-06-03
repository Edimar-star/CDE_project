resource "aws_iam_role" "step_function_role" {
  name = "step-function-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "states.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "step_function_policy" {
  name = "step-function-policy"
  role = aws_iam_role.step_function_role.id

  policy = jsonencode({
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowGlueAndSageMaker",
        "Effect": "Allow",
        "Action": [
          "lambda:InvokeFunction",
          "glue:StartCrawler",
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJobRuns",
          "glue:GetJob",
          "glue:BatchGetJobs",
          "glue:BatchGetJobRuns",
          "sagemaker:CreateTrainingJob",
          "sagemaker:DescribeTrainingJob",
          "sagemaker:AddTags",
          "events:PutRule",
          "events:PutTargets",
          "events:DescribeRule",
          "events:DeleteRule",
          "events:RemoveTargets"
        ],
        "Resource": "*"
      },
      {
        "Sid": "AllowS3Access",
        "Effect": "Allow",
        "Action": [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ],
        "Resource": [
          "arn:aws:s3:::${aws_s3_bucket.target-data-bucket.id}",
          "arn:aws:s3:::${aws_s3_bucket.target-data-bucket.id}/*"
        ]
      },
      {
        "Sid": "AllowPassRole",
        "Effect": "Allow",
        "Action": "iam:PassRole",
        "Resource": [
          "arn:aws:iam::${var.account_id}:role/glue-service-role",
          "arn:aws:iam::${var.account_id}:role/sagemaker-execution-role",
          "arn:aws:iam::${var.account_id}:role/step-function-role"
        ]
      }
    ]
  })
}

resource "aws_sfn_state_machine" "etl_workflow" {
  name     = "ETLWorkflow"
  role_arn = aws_iam_role.step_function_role.arn

  definition = jsonencode({
    StartAt: "TrainModel",
    States: {
#      LambdaTask1: {
#        Type: "Task",
#        Resource: "arn:aws:states:::lambda:invoke",
#        Parameters: {
#          FunctionName: "arn:aws:lambda:${var.aws_region}:${var.account_id}:function:etl_lambda",
#          Payload = {
#            dataset_name: "forest_fire"
#          }
#        },
#        Next: "LambdaTask2"
#      },
#      LambdaTask2: {
#        Type: "Task",
#        Resource: "arn:aws:states:::lambda:invoke",
#        Parameters: {
#          FunctionName: "arn:aws:lambda:${var.aws_region}:${var.account_id}:function:etl_lambda",
#          Payload = {
#            dataset_name: "ndvi"
#          }
#        },
#        Next: "LambdaTask3"
#      },
#      LambdaTask3: {
#        Type: "Task",
#        Resource: "arn:aws:states:::lambda:invoke",
#        Parameters: {
#          FunctionName: "arn:aws:lambda:${var.aws_region}:${var.account_id}:function:etl_lambda",
#          Payload = {
#            dataset_name: "global_climate"
#          }
#        },
#        Next: "LambdaTask4"
#      },
#      LambdaTask4: {
#        Type: "Task",
#        Resource: "arn:aws:states:::lambda:invoke",
#        Parameters: {
#          FunctionName: "arn:aws:lambda:${var.aws_region}:${var.account_id}:function:etl_lambda",
#          Payload = {
#            dataset_name: "population_density"
#          }
#        },
#        Next: "RunCrawler"
#      },
#      RunCrawler: {
#        Type: "Task",
#        Resource: "arn:aws:states:::aws-sdk:glue:startCrawler",
#        Parameters: {
#          Name: "org-report-crawler"
#        },
#        Next: "RunGlueJob"
#      },
#      RunGlueJob: {
#        Type: "Task",
#        Resource: "arn:aws:states:::glue:startJobRun.sync",
#        Parameters: {
#          JobName: "glue-job"
#        },
#        Catch: [
#          {
#            ErrorEquals: ["States.TaskFailed"],
#            ResultPath: "$.glueJobError",
#            Next: "FailGlueJob"
#          }
#        ],
#        ResultPath: "$.glueResult",
#        Next: "TrainModel"
#      },
#      FailGlueJob: {
#        Type: "Fail",
#        Error: "GlueJobFailed",
#        Cause: "El Glue Job falló"
#      },
      TrainModel: {
        Type: "Task",
        Resource: "arn:aws:states:::sagemaker:createTrainingJob.sync",
        Parameters: {
          TrainingJobName: "fires-sklearn-training-${uuid()}",
          AlgorithmSpecification: {
            TrainingInputMode: "File",
            TrainingImage: "683313688378.dkr.ecr.${var.aws_region}.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
          },
          InputDataConfig: [{
            ChannelName: "train",
            DataSource: {
              S3DataSource: {
                S3DataType: "S3Prefix",
                S3Uri: "s3://${aws_s3_bucket.target-data-bucket.id}/training",
                S3DataDistributionType: "FullyReplicated"
              }
            },
            ContentType: "text/csv"
          }],
          OutputDataConfig: {
            S3OutputPath: "s3://${aws_s3_bucket.target-data-bucket.id}/output/"
          },
          ResourceConfig: {
            InstanceType: "ml.m5.large",
            InstanceCount: 1,
            VolumeSizeInGB: 10
          },
          StoppingCondition: {
            MaxRuntimeInSeconds: 900
          },
          RoleArn: "${aws_iam_role.sagemaker_execution_role.arn}"
        },
        End: true
      }
    }
  })
}

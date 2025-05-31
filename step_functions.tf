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
    Version: "2012-10-17",
    Statement: [
      {
        Effect: "Allow",
        Action = [
          "lambda:InvokeFunction",
          "glue:StartCrawler",
          "glue:StartJobRun",
          "sagemaker:CreateTrainingJob",
          "sagemaker:DescribeTrainingJob",
          "events:PutRule",
          "events:PutTargets",
          "events:DescribeRule",
          "events:DeleteRule",
          "iam:PassRole"
        ],
        Resource: "*"
      }
    ]
  })
}

resource "aws_sfn_state_machine" "etl_workflow" {
  name     = "ETLWorkflow"
  role_arn = aws_iam_role.step_function_role.arn

  definition = jsonencode({
    StartAt: "LambdaRun",
    States: {
      LambdaRun: {
        Type: "Task",
        Resource: "arn:aws:states:::lambda:invoke",
        Parameters: {
          FunctionName: "arn:aws:lambda:${var.aws_region}:${var.account_id}:function:etl_lambda",
        },
        Next: "RunCrawler"
      },
      RunCrawler: {
        Type: "Task",
        Resource: "arn:aws:states:::aws-sdk:glue:startCrawler",
        Parameters: {
          Name: "org-report-crawler"
        },
        Next: "RunGlueJob"
      },
      RunGlueJob: {
        Type: "Task",
        Resource: "arn:aws:states:::glue:startJobRun.sync",
        Parameters: {
          JobName: "glue-job"
        },
        Next: "TrainModel"
      },
      TrainModel: {
        Type: "Task",
        Resource: "arn:aws:states:::sagemaker:createTrainingJob.sync",
        Parameters: {
          TrainingJobName: "fires-sklearn-training-$$!UUID",
          AlgorithmSpecification: {
            TrainingInputMode: "File",
            TrainingImage: "811284229777.dkr.ecr.us-west-2.amazonaws.com/sagemaker-scikit-learn:0.23-1-cpu-py3"
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

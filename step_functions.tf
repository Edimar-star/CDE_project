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
        Action: [
          "lambda:InvokeFunction",
          "glue:StartCrawler",
          "glue:StartJobRun"
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
    StartAt: "LambdaRun1",
    States: {
      LambdaRun: {
        Type: "Task",
        Resource: "arn:aws:states:::lambda:invoke",
        Parameters: {
          FunctionName: "arn:aws:lambda:${var.aws_region}:${var.account_id}:function:lambda_handler",
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
        End: true
      }
    }
  })
}

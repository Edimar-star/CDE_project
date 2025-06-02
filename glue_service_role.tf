resource "aws_iam_role" "glue_service_role" {
  name = "glue_service_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "glue.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}
resource "aws_iam_role_policy" "glue_service_role_policy" {
  name = "glue_service_role_policy"
  role = aws_iam_role.glue_service_role.name

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "glue:*",
          "s3:GetBucketLocation",
          "s3:ListBucket",
          "ec2:DescribeVpcEndpoints",
          "ec2:DescribeRouteTables",
          "ec2:CreateNetworkInterface",
          "ec2:DeleteNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSubnets",
          "ec2:DescribeVpcAttribute",
          "iam:ListRolePolicies",
          "iam:GetRole",
          "iam:GetRolePolicy",
          "cloudwatch:PutMetricData"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ],
        Resource = [
          "arn:aws:s3:::${aws_s3_bucket.code-bucket.bucket}/*",
          "arn:aws:s3:::${aws_s3_bucket.source-data-bucket.bucket}/*",
          "arn:aws:s3:::${aws_s3_bucket.target-data-bucket.bucket}/*"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

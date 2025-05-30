#!/bin/bash

set -e

region="eu-central-1"
account_id=$(aws sts get-caller-identity --query Account --output text)
security_group=$(aws ec2 describe-security-groups \
  --region "$region" \
  --filters Name=group-name,Values=redshift_sg \
  --query "SecurityGroups[0].GroupId" \
  --output text 2>/dev/null)
LATEST_ARN=$(aws lambda list-layer-versions --layer-name etl_layer \
  --region "$region" \
  --query 'LayerVersions[0].LayerVersionArn' \
  --output text)

imports=(
  # Buckets
  "aws_s3_bucket.source-data-bucket source-data-bucket-6i2caq"
  "aws_s3_bucket.target-data-bucket target-data-bucket-6i2caq"
  "aws_s3_bucket.code-bucket code-bucket-6i2caq"
  
  # Glue
  "aws_iam_role.glue_service_role glue_service_role"
  "aws_iam_role_policy.glue_service_role_policy glue_service_role:glue_service_role_policy"
  "aws_glue_catalog_database.org_report_database ${account_id}:org-report"
  "aws_glue_crawler.org_report_crawler org-report-crawler"
  "aws_glue_trigger.org_report_trigger org-report-trigger"
  "aws_glue_job.glue_job glue-job"

  # Lambda
  "aws_iam_role.lambda_exec_role lambda_exec_role"
  "aws_lambda_layer_version.etl_layer ${LATEST_ARN}"
  "aws_lambda_function.etl_lambda etl_lambda"
  
  # Redshift
  "aws_iam_role.redshift_s3_role RedshiftS3AccessRole"
  "aws_iam_role_policy_attachment.s3_access RedshiftS3AccessRole/AmazonS3ReadOnlyAccess"
  "aws_redshift_subnet_group.subnet_group redshift-subnet-group"
  "aws_security_group.redshift_sg ${security_group}" 
  "aws_redshift_cluster.main redshift-cluster"
  
  # Step functions
  "aws_iam_role.step_function_role step-function-role"
  "aws_iam_role_policy.step_function_policy step-function-role:step-function-policy"
  "aws_sfn_state_machine.etl_workflow arn:aws:states:${region}:${account_id}:stateMachine:ETLWorkflow"
)

echo "Validando importaciones Terraform..."

for imp in "${imports[@]}"
do
  echo -n "Importando $imp ... "
  if terraform import $imp 2>/dev/null; then
    echo "OK"
  else
    echo "FALLO o recurso no existe"
  fi
done

echo "Validación completa."

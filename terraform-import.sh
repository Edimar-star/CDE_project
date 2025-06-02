#!/bin/bash

set -e

region="eu-central-1"
account_id=$(aws sts get-caller-identity --query Account --output text)

# gateway ids
api_id=$(aws apigatewayv2 get-apis)
integration_id=$(aws apigatewayv2 get-integrations --api-id "${api_id}")
route_id=$(aws apigatewayv2 get-routes --api-id "${api_id}")
stage_name=$(aws apigatewayv2 get-stages --api-id "${api_id}")

imports=(
  # Buckets
  "aws_s3_bucket.source-data-bucket source-data-bucket-6i2caq"
  "aws_s3_bucket.target-data-bucket target-data-bucket-6i2caq"
  "aws_s3_bucket.code-bucket code-bucket-6i2caq"
  "aws_s3_bucket.athena_results athena-results-bucket-6i2caq"

  # Lambda ETL
  "aws_iam_role.lambda_exec_role lambda_exec_role"
  "aws_iam_role_policy.lambda_s3_write_access lambda_exec_role:lambda-s3-putobject"
  "aws_lambda_function.etl_lambda etl_lambda"
  "aws_lambda_function.etl_lambda api_lambda"

  # Glue
  "aws_iam_role.glue_service_role glue_service_role"
  "aws_iam_role_policy.glue_service_role_policy glue_service_role:glue_service_role_policy"
  "aws_glue_catalog_database.org_report_database ${account_id}:org-report"
  "aws_glue_crawler.org_report_crawler org-report-crawler"
  "aws_glue_trigger.org_report_trigger org-report-trigger"
  "aws_glue_job.glue_job glue-job"
  
  # athena
  "aws_glue_catalog_database.athena_db ${account_id}:forest_fire_data"
  "aws_glue_catalog_table.athena_table ${account_id}:forest_fire_data:fires"
  
  # Step functions
  "aws_iam_role.step_function_role step-function-role"
  "aws_iam_role_policy.step_function_policy step-function-role:step-function-policy"
  "aws_sfn_state_machine.etl_workflow arn:aws:states:${region}:${account_id}:stateMachine:ETLWorkflow"

  # Sagemark
  "aws_iam_role.sagemaker_execution_role sagemaker-execution-role"
  "aws_iam_role_policy.sagemaker_s3_access sagemaker-execution-role:sagemaker-s3-access"
  "aws_iam_role_policy_attachment.sagemaker_policy sagemaker-execution-role/sagemaker_policy"

  # API Gateway
  "terraform import aws_apigatewayv2_api.api ${api_id}"
  "terraform import aws_apigatewayv2_integration.lambda_integration ${api_id}/${integration_id}"
  "terraform import aws_apigatewayv2_route.lambda_route ${api_id}/${route_id}"
  "terraform import aws_apigatewayv2_stage.api_stage ${api_id}/${stage_name}"
  "terraform import aws_lambda_permission.allow_apigw api_lambda/AllowAPIGatewayInvoke"
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

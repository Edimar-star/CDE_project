# 1. Crear API Gateway HTTP
resource "aws_apigatewayv2_api" "api" {
  name          = "api-gateway"
  protocol_type = "HTTP"
}

# 2. Integración Lambda -> API Gateway
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                  = aws_apigatewayv2_api.api.id
  integration_type        = "AWS_PROXY"
  integration_uri         = aws_lambda_function.api_lambda.invoke_arn
  integration_method      = "GET"
  payload_format_version  = "2.0"
}

# 3. Ruta: GET /predict
resource "aws_apigatewayv2_route" "lambda_route" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "GET /predict"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# 4. Etapa de despliegue (default)
resource "aws_apigatewayv2_stage" "api_stage" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true
}

# 5. Permiso para que API Gateway invoque la Lambda
resource "aws_lambda_permission" "allow_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

output "lambda_api_url" {
  value = "${aws_apigatewayv2_api.api.api_endpoint}/predict"
}

# ------------------- IAM ROLES ------------------------

resource "aws_iam_policy" "api_gateway_lambda_access" {
  name        = "ApiGatewayLambdaMinimalAccess"
  description = "Permite gestionar API Gateway y su integración con Lambda"
  policy      = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "apigateway:GET",
          "apigateway:POST",
          "apigateway:PUT",
          "apigateway:PATCH",
          "apigateway:DELETE",
          "lambda:GetFunction",
          "lambda:InvokeFunction",
          "lambda:CreateFunction",
          "lambda:UpdateFunctionCode",
          "lambda:UpdateFunctionConfiguration",
          "iam:PassRole"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_policy_attachment" "attach_policy_to_user" {
  name       = "attach-apigateway-lambda"
  users      = ["DEP_user"] # Cambia esto si estás usando un role
  policy_arn = aws_iam_policy.api_gateway_lambda_access.arn
}
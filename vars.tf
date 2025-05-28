variable "aws_region" {
  description = "AWS region to deploy resources"
  default     = "us-east-1"
}

variable "account_id" {
  description = "ID of my account"
  default     = "914194815712"
}

variable "glue_scripts" {
  default = {
    "main.py" = "glue/main.py"
  }
}
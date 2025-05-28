provider "aws" {
  region = var.aws_region
}

# Role para Redshift con permisos de lectura en S3
resource "aws_iam_role" "redshift_s3_role" {
  name = "RedshiftS3AccessRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {
        Service = "redshift.amazonaws.com"
      },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "s3_access" {
  role       = aws_iam_role.redshift_s3_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "public1" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true
}

resource "aws_subnet" "public2" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = true
}

resource "aws_redshift_subnet_group" "subnet_group" {
  name       = "redshift-subnet-group"
  subnet_ids = [aws_subnet.public1.id, aws_subnet.public2.id]
}

# Security Group para acceso a Redshift
resource "aws_security_group" "redshift_sg" {
  name   = "redshift_sg"
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 5439
    to_port     = 5439
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Restringe en producción
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Redshift cluster
resource "aws_redshift_cluster" "main" {
  cluster_identifier       = "redshift-cluster"
  database_name            = "forest_fire_data"
  master_username          = "adminuser"
  master_password          = "password1234"
  node_type                = "dc2.large"
  number_of_nodes          = 1
  publicly_accessible      = true
  skip_final_snapshot      = true
  iam_roles                = [aws_iam_role.redshift_s3_role.arn]
  cluster_subnet_group_name = aws_redshift_subnet_group.subnet_group.name
  vpc_security_group_ids   = [aws_security_group.redshift_sg.id]
}

output "redshift_endpoint" {
  value = aws_redshift_cluster.main.endpoint
}

output "redshift_role_arn" {
  value = aws_iam_role.redshift_s3_role.arn
}

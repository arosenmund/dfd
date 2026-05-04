terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name = "${var.project_name}-${var.environment}"
  azs  = slice(data.aws_availability_zones.available.names, 0, 2)
}

resource "aws_vpc" "this" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name = "${local.name}-vpc"
  }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.this.id
  cidr_block        = "10.0.${count.index + 1}.0/24"
  availability_zone = local.azs[count.index]
  tags = {
    Name = "${local.name}-private-${count.index + 1}"
  }
}

resource "aws_security_group" "rds" {
  name   = "${local.name}-rds-sg"
  vpc_id = aws_vpc.this.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_subnet_group" "this" {
  name       = "${local.name}-db-subnets"
  subnet_ids = aws_subnet.private[*].id
}

resource "random_password" "db" {
  length  = 24
  special = false
}

resource "aws_db_instance" "this" {
  identifier              = "${local.name}-postgres"
  engine                  = "postgres"
  engine_version          = "16"
  instance_class          = var.db_instance_class
  allocated_storage       = 20
  max_allocated_storage   = 100
  db_name                 = var.db_name
  username                = var.db_username
  password                = random_password.db.result
  db_subnet_group_name    = aws_db_subnet_group.this.name
  vpc_security_group_ids  = [aws_security_group.rds.id]
  skip_final_snapshot     = true
  deletion_protection     = false
  backup_retention_period = 7
  multi_az                = false
  publicly_accessible     = false
  storage_encrypted       = true
}

resource "aws_s3_bucket" "uploads" {
  bucket_prefix = "${local.name}-uploads-"
}

resource "aws_s3_bucket" "results" {
  bucket_prefix = "${local.name}-results-"
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket                  = aws_s3_bucket.uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "results" {
  bucket                  = aws_s3_bucket.results.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_apprunner_auto_scaling_configuration_version" "this" {
  auto_scaling_configuration_name = "${local.name}-as"
  max_concurrency                 = 100
  max_size                        = 3
  min_size                        = 1
}

resource "aws_iam_role" "apprunner_access" {
  name = "${local.name}-apprunner-ecr-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "build.apprunner.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_ecr" {
  role       = aws_iam_role.apprunner_access.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

resource "aws_apprunner_service" "api" {
  service_name = "${local.name}-api"

  source_configuration {
    auto_deployments_enabled = false

    authentication_configuration {
      access_role_arn = aws_iam_role.apprunner_access.arn
    }

    image_repository {
      image_repository_type = "ECR"
      image_identifier      = var.app_image

      image_configuration {
        port = tostring(var.app_port)
        runtime_environment_variables = {
          APP_ENV      = var.environment
          APP_NAME     = "Deepfake Detection API"
          PORT         = tostring(var.app_port)
          DATABASE_URL = "postgresql://${var.db_username}:${random_password.db.result}@${aws_db_instance.this.address}:5432/${var.db_name}"
        }
      }
    }
  }

  instance_configuration {
    cpu    = var.app_cpu
    memory = var.app_memory
  }

  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.this.arn
}

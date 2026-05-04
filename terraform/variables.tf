variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project prefix"
  type        = string
  default     = "dfd"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "app_image" {
  description = "Full ECR image URI and tag, e.g. 123456789012.dkr.ecr.us-east-1.amazonaws.com/dfd:latest"
  type        = string
}

variable "app_port" {
  description = "Container listening port"
  type        = number
  default     = 8000
}

variable "app_cpu" {
  description = "App Runner vCPU setting"
  type        = string
  default     = "0.25 vCPU"
}

variable "app_memory" {
  description = "App Runner memory setting"
  type        = string
  default     = "0.5 GB"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.micro"
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "dfd"
}

variable "db_username" {
  description = "PostgreSQL admin username"
  type        = string
  default     = "dfd_admin"
}

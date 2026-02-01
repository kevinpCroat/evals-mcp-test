variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g. development, production)"
  type        = string
  default     = "development"
}

variable "project_name" {
  description = "Project name for resource naming and tags"
  type        = string
  default     = "task-management-api"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "container_image" {
  description = "ECR image URI for the task management API container"
  type        = string
  default     = "123456789012.dkr.ecr.us-east-1.amazonaws.com/task-management-api:latest"
}

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "taskdb"
}

variable "db_username" {
  description = "Master username for RDS (password from Secrets Manager)"
  type        = string
  default     = "postgres"
}

variable "ecs_task_cpu" {
  description = "CPU units for ECS Fargate task (256 = 0.25 vCPU)"
  type        = number
  default     = 256
}

variable "ecs_task_memory_mb" {
  description = "Memory in MB for ECS Fargate task"
  type        = number
  default     = 512
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "app_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8000
}

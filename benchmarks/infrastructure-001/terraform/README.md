# Task Management API - Terraform Infrastructure

## Overview

This Terraform code provisions AWS infrastructure for the Task Management API: a containerized Flask application running on ECS Fargate, with RDS PostgreSQL, S3, ALB, Secrets Manager, and CloudWatch.

## Prerequisites

- Terraform 1.5+
- AWS CLI configured (for `terraform plan`; not required for validate-only)

## Usage

### Initialize Terraform

```bash
terraform init
```

For verification without a backend:

```bash
terraform init -backend=false
```

### Validate Configuration

```bash
terraform validate
```

### Plan Infrastructure

```bash
terraform plan
```

### Apply (DO NOT RUN for this exercise)

```bash
terraform apply
```

## Architecture

- **VPC**: 10.0.0.0/16 with public subnets (ALB) and private subnets (ECS, RDS) across 2 AZs; NAT Gateway for private outbound.
- **Compute**: ECS Fargate cluster with a service (2 tasks), task definition using placeholder ECR image.
- **Load balancing**: Application Load Balancer with HTTP listener and target group; health check on `/health`.
- **Database**: RDS PostgreSQL 15 (db.t3.micro, multi-AZ), in private subnets; credentials in Secrets Manager.
- **Storage**: S3 bucket with versioning, AES-256 encryption, and lifecycle rule for `archived/` prefix.
- **Security**: Security groups for ALB (80/443), ECS (app port from ALB only), RDS (5432 from ECS only); IAM roles for ECS execution and task (S3 + Secrets Manager).
- **Monitoring**: CloudWatch log group for ECS; alarms for RDS CPU, ECS task count, and ALB 5xx.

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| aws_region | us-east-1 | AWS region |
| environment | development | Environment name |
| project_name | task-management-api | Project name |
| vpc_cidr | 10.0.0.0/16 | VPC CIDR |
| container_image | (placeholder ECR URI) | ECS container image |
| db_name | taskdb | PostgreSQL database name |
| db_username | postgres | RDS master username |
| ecs_task_cpu | 256 | ECS task CPU units |
| ecs_task_memory_mb | 512 | ECS task memory (MB) |
| ecs_desired_count | 2 | Desired ECS task count |
| app_port | 8000 | Container port |

## Outputs

- `vpc_id` - VPC ID
- `alb_dns_name` - ALB DNS name
- `ecs_cluster_name` - ECS cluster name
- `ecs_service_name` - ECS service name
- `rds_endpoint` - RDS endpoint
- `s3_bucket_name` - S3 bucket name
- `db_secret_arn` - Secrets Manager secret ARN for DB credentials

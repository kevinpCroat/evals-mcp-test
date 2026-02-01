# RDS PostgreSQL

resource "aws_db_subnet_group" "main" {
  name        = "${var.project_name}-rds-subnet-group"
  description = "Subnet group for RDS"
  subnet_ids  = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-rds-subnet-group"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "${var.project_name}-db"
  engine         = "postgres"
  engine_version = "15"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  storage_type         = "gp3"
  storage_encrypted     = true
  multi_az             = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db.result
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "Mon:04:00-Mon:05:00"

  skip_final_snapshot = true

  tags = {
    Name = "${var.project_name}-rds"
  }
}

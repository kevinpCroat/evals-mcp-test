# Database credentials in Secrets Manager (no hardcoded passwords)

resource "random_password" "db" {
  length           = 32
  special         = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "db" {
  name        = "${var.project_name}/db-credentials"
  description = "RDS PostgreSQL credentials for Task Management API"

  tags = {
    Name = "${var.project_name}-db-secret"
  }
}

# Store username/password only; app gets host/port from task definition env (from RDS outputs)
resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db.result
    dbname   = var.db_name
    port     = "5432"
  })
}

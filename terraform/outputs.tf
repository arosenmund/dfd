output "app_url" {
  value       = aws_apprunner_service.api.service_url
  description = "Public URL of the API"
}

output "uploads_bucket" {
  value       = aws_s3_bucket.uploads.bucket
  description = "Bucket for uploaded files"
}

output "results_bucket" {
  value       = aws_s3_bucket.results.bucket
  description = "Bucket for analysis results"
}

output "database_endpoint" {
  value       = aws_db_instance.this.address
  description = "RDS endpoint hostname"
}

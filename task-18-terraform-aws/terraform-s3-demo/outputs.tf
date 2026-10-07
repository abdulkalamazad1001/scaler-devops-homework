output "bucket_name" {
  description = "Name of the bucket, including the random suffix."
  value       = aws_s3_bucket.demo.bucket
}

output "bucket_arn" {
  description = "ARN of the bucket, for use in IAM policies."
  value       = aws_s3_bucket.demo.arn
}

output "bucket_region" {
  description = "Region the bucket lives in."
  value       = aws_s3_bucket.demo.region
}

output "bucket_regional_domain_name" {
  description = "Regional endpoint of the bucket."
  value       = aws_s3_bucket.demo.bucket_regional_domain_name
}

output "versioning_status" {
  description = "Versioning status of the bucket."
  value       = aws_s3_bucket_versioning.demo.versioning_configuration[0].status
}

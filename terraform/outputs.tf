output "table_name" {
  description = "Name of the DynamoDB job table."
  value       = aws_dynamodb_table.jobs.name
}

output "table_arn" {
  description = "ARN of the DynamoDB job table."
  value       = aws_dynamodb_table.jobs.arn
}

output "team_jobs_index_name" {
  description = "Name of the index used to query a team's jobs."
  value       = "TeamJobsIndex"
}

output "iam_policy_arn" {
  description = "ARN of the least-privilege job tracker IAM policy."
  value       = aws_iam_policy.job_tracker_access.arn
}

output "runtime_role_arn" {
  description = "ARN of the IAM role used by the job tracker application."
  value       = aws_iam_role.job_tracker_runtime.arn
}

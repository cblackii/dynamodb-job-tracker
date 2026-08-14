variable "aws_region" {
  description = "AWS Region used for the sandbox deployment."
  type        = string
  default     = "us-west-2"
}

variable "runtime_trusted_principal_arn" {
  description = "IAM principal permitted to assume the job tracker runtime role."
  type        = string
  sensitive   = true

  validation {
    condition     = can(regex("^arn:aws:iam::[0-9]{12}:user/.+$", var.runtime_trusted_principal_arn))
    error_message = "runtime_trusted_principal_arn must be a valid IAM user ARN."
  }
}

variable "project_name" {
  description = "Lowercase name used to identify project resources."
  type        = string
  default     = "cloud-automation-job-tracker"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,40}$", var.project_name))
    error_message = "project_name must start with a letter and contain only lowercase letters, numbers, or hyphens."
  }
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "test", "prod"], var.environment)
    error_message = "environment must be dev, test, or prod."
  }
}

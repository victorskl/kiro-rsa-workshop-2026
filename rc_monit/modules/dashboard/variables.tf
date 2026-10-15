# ---------------------------------------------------------------------------
# modules/dashboard/variables.tf
# ---------------------------------------------------------------------------

variable "dashboard_name" {
  description = "Name of the CloudWatch dashboard."
  type        = string
  default     = "ResearchComputing"
}

variable "aws_region" {
  description = "AWS region where the dashboard is deployed."
  type        = string
}

variable "research_projects" {
  description = "List of research project identifiers to include as metric dimensions."
  type        = list(string)
}

variable "s3_research_bucket_names" {
  description = "List of S3 bucket names to show in the storage panel."
  type        = list(string)
  default     = []
}

variable "efs_filesystem_ids" {
  description = "List of EFS filesystem IDs to show in the storage panel."
  type        = list(string)
  default     = []
}

variable "source_account_ids" {
  description = "List of source account IDs for cross-account metric queries (OAM)."
  type        = list(string)
  default     = []
}

variable "cpu_idle_threshold" {
  description = "CPU utilization (%) below which instances are flagged as idle."
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tag map applied to all resources in this module."
  type        = map(string)
  default     = {}
}

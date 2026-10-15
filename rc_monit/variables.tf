# ---------------------------------------------------------------------------
# variables.tf — root module
# ---------------------------------------------------------------------------

# ── AWS / account ──────────────────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region where the monitoring resources are deployed."
  type        = string
  default     = "us-east-1"
}

variable "monitoring_account_role_arn" {
  description = <<-EOT
    IAM role ARN to assume in the monitoring account.
    Leave empty when Terraform is already authenticated as that account.
  EOT
  type        = string
  default     = ""
}

variable "management_account_role_arn" {
  description = <<-EOT
    IAM role ARN to assume in the AWS Organizations management account.
    Required to activate cost-allocation tags via Cost Explorer.
  EOT
  type        = string
  default     = ""
}

variable "source_account_ids" {
  description = <<-EOT
    List of AWS account IDs whose metrics are shared into the monitoring
    account via CloudWatch OAM.  Include the monitoring account itself if
    its EC2 metrics should also appear in the dashboard.
  EOT
  type        = list(string)
  default     = []
}

# ── Tagging ────────────────────────────────────────────────────────────────

variable "default_project" {
  description = "Default value for the Project tag applied to shared infrastructure."
  type        = string
  default     = "research-platform"
}

variable "default_researcher" {
  description = "Default value for the Researcher tag applied to shared infrastructure."
  type        = string
  default     = "platform-team"
}

variable "default_team" {
  description = "Default value for the Team tag applied to shared infrastructure."
  type        = string
  default     = "computational-bio"
}

variable "environment" {
  description = "Deployment environment (prod | staging | dev)."
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["prod", "staging", "dev"], var.environment)
    error_message = "environment must be one of: prod, staging, dev."
  }
}

variable "default_pipeline" {
  description = "Default value for the Pipeline tag on shared infrastructure."
  type        = string
  default     = "platform"
}

variable "cost_center" {
  description = "Finance cost-center code applied to all resources."
  type        = string
  default     = "CC-0000"
}

# ── Projects ───────────────────────────────────────────────────────────────

variable "research_projects" {
  description = <<-EOT
    List of active research project identifiers.  Used to parameterise
    dashboard widgets and per-project cost alarms.
  EOT
  type        = list(string)
  default     = ["genome-seq", "protein-fold", "climate-model"]
}

# ── Alarms ─────────────────────────────────────────────────────────────────

variable "cost_alarm_threshold_usd" {
  description = "Daily spend (USD) per project that triggers the cost alarm."
  type        = number
  default     = 500
}

variable "cpu_idle_threshold_percent" {
  description = "CPUUtilization (%) below which an instance is considered idle."
  type        = number
  default     = 10
}

variable "spot_interruption_alarm_threshold" {
  description = "Number of spot interruptions in one hour that triggers the alarm."
  type        = number
  default     = 5
}

# ── Notifications ──────────────────────────────────────────────────────────

variable "slack_webhook_secret_name" {
  description = "Name of the AWS Secrets Manager secret that stores the Slack webhook URL."
  type        = string
  default     = "research-monitoring/slack-webhook"
}

variable "alarm_email_addresses" {
  description = "Optional list of email addresses to also subscribe to the alarms SNS topic."
  type        = list(string)
  default     = []
}

# ── Dashboard ──────────────────────────────────────────────────────────────

variable "dashboard_name" {
  description = "Name of the CloudWatch dashboard."
  type        = string
  default     = "ResearchComputing"
}

variable "efs_filesystem_ids" {
  description = "List of EFS filesystem IDs to include in the storage panel."
  type        = list(string)
  default     = []
}

variable "s3_research_bucket_names" {
  description = "List of S3 bucket names to include in the storage panel."
  type        = list(string)
  default     = []
}

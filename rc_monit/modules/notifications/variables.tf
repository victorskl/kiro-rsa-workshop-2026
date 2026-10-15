# ---------------------------------------------------------------------------
# modules/notifications/variables.tf
# ---------------------------------------------------------------------------

variable "slack_webhook_secret_name" {
  description = "Name of the Secrets Manager secret containing the Slack incoming webhook URL."
  type        = string
  default     = "research-monitoring/slack-webhook"
}

variable "alarm_email_addresses" {
  description = "Optional list of email addresses subscribed directly to the SNS alarms topic."
  type        = list(string)
  default     = []
}

variable "dashboard_url" {
  description = <<-EOT
    Direct URL to the CloudWatch dashboard, injected into Slack alarm messages.
    If left empty, the module constructs the URL from dashboard_name and aws_region.
  EOT
  type        = string
  default     = ""
}

variable "dashboard_name" {
  description = "CloudWatch dashboard name, used to construct the dashboard URL."
  type        = string
  default     = "ResearchComputing"
}

variable "aws_region" {
  description = "AWS region, used to construct the dashboard URL."
  type        = string
  default     = "us-east-1"
}

variable "tags" {
  description = "Tag map applied to all resources in this module."
  type        = map(string)
  default     = {}
}

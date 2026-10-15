# ---------------------------------------------------------------------------
# modules/alarms/variables.tf
# ---------------------------------------------------------------------------

variable "research_projects" {
  description = "List of research project identifiers. One cost and one spot alarm is created per project."
  type        = list(string)
}

variable "cost_alarm_threshold_usd" {
  description = "Daily spend (USD) per project that triggers the cost spike alarm."
  type        = number
  default     = 500
}

variable "cpu_idle_threshold_percent" {
  description = "CPUUtilization (%) below which an instance is flagged as idle."
  type        = number
  default     = 10
}

variable "spot_interruption_alarm_threshold" {
  description = "Number of spot interruptions within one hour that triggers the burst alarm."
  type        = number
  default     = 5
}

variable "sns_topic_arn" {
  description = "ARN of the SNS topic that receives alarm notifications."
  type        = string
}

variable "tags" {
  description = "Tag map applied to all resources in this module."
  type        = map(string)
  default     = {}
}

# ---------------------------------------------------------------------------
# modules/cost_harvester/variables.tf
# ---------------------------------------------------------------------------

variable "aws_region" {
  description = "AWS region for CloudWatch metric publishing."
  type        = string
}

variable "research_projects" {
  description = "List of research project identifiers passed to the Lambda as an env var."
  type        = list(string)
}

variable "tags" {
  description = "Tag map applied to all resources in this module."
  type        = map(string)
  default     = {}
}

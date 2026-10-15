# ---------------------------------------------------------------------------
# modules/oam/variables.tf
# ---------------------------------------------------------------------------

variable "source_account_ids" {
  description = <<-EOT
    List of AWS account IDs that are permitted to create OAM links into the
    monitoring sink.  Include all member/research accounts whose metrics
    should appear in the centralised CloudWatch dashboard.
  EOT
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tag map applied to all resources in this module."
  type        = map(string)
  default     = {}
}

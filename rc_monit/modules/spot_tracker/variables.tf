# ---------------------------------------------------------------------------
# modules/spot_tracker/variables.tf
# ---------------------------------------------------------------------------

variable "tags" {
  description = "Tag map applied to all resources in this module."
  type        = map(string)
  default     = {}
}

# ---------------------------------------------------------------------------
# modules/tagging/main.tf
#
# Validates that all required tag values are non-empty and produces a
# merged tag map ready for use in provider default_tags or resource tags.
# ---------------------------------------------------------------------------

locals {
  required_tags = {
    Project     = var.project
    Researcher  = var.researcher
    Team        = var.team
    Environment = var.environment
    Pipeline    = var.pipeline
    CostCenter  = var.cost_center
  }

  # Merge required tags with any caller-supplied extras; required tags win.
  tags = merge(var.additional_tags, local.required_tags)

  # Validation: collect any required tag keys whose value is empty.
  empty_keys = [
    for k, v in local.required_tags : k if trimspace(v) == ""
  ]
}

# Emit a clear error at plan time when a required tag is missing.
resource "terraform_data" "tag_validation" {
  lifecycle {
    precondition {
      condition     = length(local.empty_keys) == 0
      error_message = "The following required tags have empty values: ${join(", ", local.empty_keys)}"
    }
  }
}

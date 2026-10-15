# ---------------------------------------------------------------------------
# providers.tf
#
# Two AWS provider aliases:
#   - default ("monitoring")  — the account that owns the CloudWatch dashboard,
#                               SNS topics, alarms, and OAM sink.
#   - "management"            — the AWS Organizations management account that
#                               owns Cost Explorer and activates cost-allocation
#                               tags.
#
# Set the role ARNs in terraform.tfvars (or via TF_VAR_* env vars).
# ---------------------------------------------------------------------------

provider "aws" {
  region = var.aws_region

  # Assume a cross-account role in the monitoring account when running from
  # a CI/CD pipeline or a developer workstation.  Leave assume_role empty
  # (or omit it) when already authenticated as the monitoring account.
  dynamic "assume_role" {
    for_each = var.monitoring_account_role_arn != "" ? [1] : []
    content {
      role_arn     = var.monitoring_account_role_arn
      session_name = "terraform-research-monitoring"
    }
  }

  default_tags {
    tags = module.tags.tags
  }
}

# Provider alias used only by the cost_allocation_tags module, which must
# run in the AWS Organizations management account.
provider "aws" {
  alias  = "management"
  region = var.aws_region

  dynamic "assume_role" {
    for_each = var.management_account_role_arn != "" ? [1] : []
    content {
      role_arn     = var.management_account_role_arn
      session_name = "terraform-research-management"
    }
  }

  default_tags {
    tags = module.tags.tags
  }
}

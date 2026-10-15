# ---------------------------------------------------------------------------
# modules/cost_allocation_tags/main.tf
#
# Activates the research-computing tag keys in AWS Cost Explorer so that
# cost-by-tag reporting is available.
#
# IMPORTANT: This module must run in the AWS Organizations management account
# (use the "management" provider alias from the root module).
#
# NOTE: After activation there is a 24-hour delay before Cost Explorer
# surfaces historical data for the newly activated tags.
# ---------------------------------------------------------------------------

terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

locals {
  # The tag keys we want to track in Cost Explorer.
  tag_keys = [
    "Project",
    "Researcher",
    "Team",
    "Environment",
    "Pipeline",
    "CostCenter",
  ]
}

# Activate each tag key as a cost-allocation tag.
# aws_ce_cost_allocation_tag requires the tag key and a status of "Active".
resource "aws_ce_cost_allocation_tag" "research_tags" {
  for_each = toset(local.tag_keys)

  tag_key = each.key
  status  = "Active"
}

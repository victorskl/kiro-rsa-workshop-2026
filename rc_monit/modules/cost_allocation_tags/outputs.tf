# ---------------------------------------------------------------------------
# modules/cost_allocation_tags/outputs.tf
# ---------------------------------------------------------------------------

output "activated_tag_keys" {
  description = "List of tag keys activated as cost-allocation tags in Cost Explorer."
  value       = [for t in aws_ce_cost_allocation_tag.research_tags : t.tag_key]
}

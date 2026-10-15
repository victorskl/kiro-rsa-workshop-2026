# ---------------------------------------------------------------------------
# modules/tagging/outputs.tf
# ---------------------------------------------------------------------------

output "tags" {
  description = "Merged and validated tag map for use in default_tags or resource tags blocks."
  value       = local.tags
}

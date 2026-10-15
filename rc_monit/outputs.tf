# ---------------------------------------------------------------------------
# outputs.tf — root module
# ---------------------------------------------------------------------------

# ── Dashboard ──────────────────────────────────────────────────────────────

output "dashboard_url" {
  description = "Direct URL to the ResearchComputing CloudWatch dashboard in the AWS console."
  value       = module.dashboard.dashboard_url
}

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard."
  value       = module.dashboard.dashboard_name
}

# ── Notifications ──────────────────────────────────────────────────────────

output "sns_topic_arn" {
  description = "ARN of the SNS topic that receives CloudWatch alarm notifications."
  value       = module.notifications.sns_topic_arn
}

output "slack_webhook_secret_arn" {
  description = "ARN of the Secrets Manager secret for the Slack webhook URL. Populate after deploy."
  value       = module.notifications.slack_webhook_secret_arn
}

# ── Lambda functions ───────────────────────────────────────────────────────

output "cost_harvester_lambda_name" {
  description = "Name of the Cost Harvester Lambda function."
  value       = module.cost_harvester.lambda_function_name
}

output "spot_tracker_lambda_name" {
  description = "Name of the Spot Tracker Lambda function."
  value       = module.spot_tracker.lambda_function_name
}

output "slack_notifier_lambda_name" {
  description = "Name of the Slack Notifier Lambda function."
  value       = module.notifications.lambda_function_name
}

# ── Alarms ─────────────────────────────────────────────────────────────────

output "cost_spike_alarm_names" {
  description = "Names of the per-project daily cost spike alarms."
  value       = module.alarms.cost_spike_alarm_names
}

output "spot_burst_alarm_names" {
  description = "Names of the per-project spot interruption burst alarms."
  value       = module.alarms.spot_burst_alarm_names
}

# ── Cost Explorer ──────────────────────────────────────────────────────────

output "activated_cost_tag_keys" {
  description = "Tag keys activated as cost-allocation tags in Cost Explorer."
  value       = module.cost_allocation_tags.activated_tag_keys
}

# ── OAM ────────────────────────────────────────────────────────────────────

output "oam_sink_arn" {
  description = "ARN of the CloudWatch OAM sink. Share with source-account teams to create OAM links."
  value       = module.oam.sink_arn
}

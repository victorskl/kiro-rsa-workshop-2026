# ---------------------------------------------------------------------------
# modules/oam/outputs.tf
# ---------------------------------------------------------------------------

output "sink_arn" {
  description = "ARN of the CloudWatch OAM sink in the monitoring account."
  value       = aws_oam_sink.monitoring.arn
}

output "sink_id" {
  description = "ID of the CloudWatch OAM sink (used when creating source-account links)."
  value       = aws_oam_sink.monitoring.id
}

# ---------------------------------------------------------------------------
# modules/alarms/outputs.tf
# ---------------------------------------------------------------------------

output "cost_spike_alarm_names" {
  description = "Names of the per-project cost spike alarms."
  value       = [for a in aws_cloudwatch_metric_alarm.cost_spike : a.alarm_name]
}

output "ec2_idle_alarm_name" {
  description = "Name of the EC2 idle CPU alarm."
  value       = aws_cloudwatch_metric_alarm.ec2_idle.alarm_name
}

output "spot_burst_alarm_names" {
  description = "Names of the per-project spot interruption burst alarms."
  value       = [for a in aws_cloudwatch_metric_alarm.spot_burst : a.alarm_name]
}

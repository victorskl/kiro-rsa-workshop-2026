# ---------------------------------------------------------------------------
# modules/alarms/main.tf
#
# Creates three classes of CloudWatch alarms:
#   1. Daily cost spike per project (ResearchComputing/Costs)
#   2. Idle EC2 instance (CPUUtilization < threshold for 2+ hours)
#   3. Spot interruption burst (> N interruptions in 1 hour)
#
# All alarms publish to the shared SNS topic provided by the notifications
# module.
# ---------------------------------------------------------------------------

locals {
  # Alarm name prefixes
  cost_prefix = "research-cost-spike"
  idle_prefix = "research-ec2-idle"
  spot_prefix = "research-spot-burst"
}

# ── 1. Daily cost spike per project ───────────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "cost_spike" {
  for_each = toset(var.research_projects)

  alarm_name          = "${local.cost_prefix}-${each.key}"
  alarm_description   = "Daily spend for project ${each.key} exceeded $${var.cost_alarm_threshold_usd} USD"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "DailySpend"
  namespace           = "ResearchComputing/Costs"
  period              = 86400 # 1 day
  statistic           = "Sum"
  threshold           = var.cost_alarm_threshold_usd
  treat_missing_data  = "notBreaching"

  dimensions = {
    Project = each.key
  }

  alarm_actions = [var.sns_topic_arn]
  ok_actions    = [var.sns_topic_arn]

  tags = var.tags
}

# ── 2. Idle EC2 instance (low CPU) ────────────────────────────────────────
#
# Note: This alarm fires on *any* EC2 instance in the account with CPU
# below the threshold.  In production, scope it further with Auto Scaling
# Group dimensions or per-instance alarms via aws_autoscaling_lifecycle_hook.

resource "aws_cloudwatch_metric_alarm" "ec2_idle" {
  alarm_name          = local.idle_prefix
  alarm_description   = "One or more EC2 instances have CPU < ${var.cpu_idle_threshold_percent}% for 2+ hours — possible idle waste"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 24 # 24 × 5-min periods = 2 hours
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300 # 5 minutes
  statistic           = "Average"
  threshold           = var.cpu_idle_threshold_percent
  treat_missing_data  = "notBreaching"

  alarm_actions = [var.sns_topic_arn]
  ok_actions    = [var.sns_topic_arn]

  tags = var.tags
}

# ── 3. Spot interruption burst per project ─────────────────────────────────

resource "aws_cloudwatch_metric_alarm" "spot_burst" {
  for_each = toset(var.research_projects)

  alarm_name          = "${local.spot_prefix}-${each.key}"
  alarm_description   = "Project ${each.key} exceeded ${var.spot_interruption_alarm_threshold} spot interruptions in 1 hour"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "SpotInterruption"
  namespace           = "ResearchComputing/Spot"
  period              = 3600 # 1 hour
  statistic           = "Sum"
  threshold           = var.spot_interruption_alarm_threshold
  treat_missing_data  = "notBreaching"

  dimensions = {
    Project = each.key
  }

  alarm_actions = [var.sns_topic_arn]
  ok_actions    = [var.sns_topic_arn]

  tags = var.tags
}

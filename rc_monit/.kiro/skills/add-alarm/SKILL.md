---
name: add-alarm
description: Add a new CloudWatch alarm to the research monitoring stack. Use when a new threshold or metric needs to trigger a Slack notification.
---

## Guidelines

- All new alarms go in `modules/alarms/main.tf`
- Always set `treat_missing_data = "notBreaching"` — research workloads are bursty and metric gaps must not trigger false alarms
- All alarms must target `var.sns_topic_arn` as the `alarm_actions` value — never hardcode an ARN
- Per-project alarms use `for_each = toset(var.research_projects)` so they scale automatically when new projects are added
- Custom-namespace metrics (`ResearchComputing/*`) require the harvester Lambda to be publishing before the alarm will leave `INSUFFICIENT_DATA` state

## Steps

1. Add the alarm resource to `modules/alarms/main.tf`:
   ```hcl
   resource "aws_cloudwatch_metric_alarm" "my_new_alarm" {
     for_each = toset(var.research_projects)  # omit if not per-project

     alarm_name          = "research-<type>-${each.key}"
     alarm_description   = "..."
     comparison_operator = "GreaterThanThreshold"  # or LessThanThreshold
     evaluation_periods  = 1
     metric_name         = "<MetricName>"
     namespace           = "ResearchComputing/Costs"  # or AWS/EC2, ResearchComputing/Spot
     period              = 3600
     statistic           = "Sum"
     threshold           = var.my_threshold
     treat_missing_data  = "notBreaching"

     dimensions = {
       Project = each.key  # omit if not per-project
     }

     alarm_actions = [var.sns_topic_arn]
     ok_actions    = [var.sns_topic_arn]
     tags          = var.tags
   }
   ```

2. Add the threshold as a variable in `modules/alarms/variables.tf` if it should be configurable.

3. Add the threshold variable to root `variables.tf` and wire it through in root `main.tf`.

4. Expose the new alarm name(s) in `modules/alarms/outputs.tf`:
   ```hcl
   output "my_new_alarm_names" {
     value = [for a in aws_cloudwatch_metric_alarm.my_new_alarm : a.alarm_name]
   }
   ```

5. Expose the output in root `outputs.tf`.

6. Run `terraform plan` to verify, then `terraform apply`.

## Alarm Period Reference

| Metric source | Recommended period | Rationale |
|---|---|---|
| `ResearchComputing/Costs` DailySpend | 86400 (1 day) | Cost Explorer data is daily granularity |
| `ResearchComputing/Spot` SpotInterruption | 3600 (1 hour) | Detect burst interruptions quickly |
| `AWS/EC2` CPUUtilization | 300 (5 min) | Native metric resolution |
| `AWS/EFS` PermittedThroughput | 300 (5 min) | Native metric resolution |

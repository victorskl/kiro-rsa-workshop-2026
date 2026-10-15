# Monitoring and Alerting Conventions

- All CloudWatch alarms publish to the single shared SNS topic from modules/notifications.
- New metric types go into one of two custom namespaces: ResearchComputing/Costs or ResearchComputing/Spot. Do not create additional custom namespaces.
- treat_missing_data = "notBreaching" on all alarms — research workloads are bursty and gaps in metrics should not trigger false alarms.
- Cost alarms use period = 86400 (daily granularity) to match Cost Explorer data resolution.
- Spot interruption alarms use period = 3600 (hourly) to detect burst events quickly.
- The Slack notifier Lambda reads the webhook URL from Secrets Manager on every cold start and caches it in-process. To rotate the webhook, update the secret — do not redeploy the Lambda unless forcing a cache flush.
- OAM sink policy must be updated when adding a new member account. Add the account ID to source_account_ids in terraform.tfvars and re-apply.

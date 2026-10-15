---
name: rotate-slack-webhook
description: Rotate the Slack incoming webhook URL stored in Secrets Manager. Use when a webhook URL is compromised, expires, or a Slack app is being reconfigured. Does not require a Terraform apply.
---

## Steps

1. Generate a new incoming webhook URL in your Slack workspace:
   - Go to **Slack App settings → Incoming Webhooks → Add New Webhook**
   - Copy the new URL (`https://hooks.slack.com/services/T.../B.../...`)

2. Update the Secrets Manager secret — **do NOT modify `terraform.tfvars` or re-run `terraform apply`**:
   ```bash
   aws secretsmanager put-secret-value \
     --secret-id research-monitoring/slack-webhook \
     --secret-string '{"webhook_url":"https://hooks.slack.com/services/NEW_URL"}'
   ```

3. Force the Lambda to pick up the new URL by touching its configuration
   (the Lambda caches the webhook URL in-process on warm invocations):
   ```bash
   aws lambda update-function-configuration \
     --function-name research-slack-notifier \
     --description "webhook-rotation-$(date +%s)"
   ```

4. Validate delivery by publishing a test SNS message:
   ```bash
   aws sns publish \
     --topic-arn "$(terraform output -raw sns_topic_arn)" \
     --message '{"AlarmName":"test-rotation","NewStateValue":"ALARM","NewStateReason":"Webhook rotation test","Trigger":{"MetricName":"DailySpend","Namespace":"ResearchComputing/Costs","Threshold":500,"Dimensions":[{"name":"Project","value":"test"}]}}'
   ```
   Confirm a Slack message arrives in the configured channel.

5. Revoke the old webhook URL in Slack app settings.

## Notes

- The `lifecycle { ignore_changes = [secret_string] }` block on the Secrets Manager resource means subsequent `terraform apply` runs will **not** overwrite the real URL with `REPLACE_ME`.
- Never store the webhook URL in `terraform.tfvars` or version control — it grants unauthenticated posting access to the Slack channel.
- The Lambda log group is `/aws/lambda/research-slack-notifier`. Check it if Slack messages are not arriving after rotation.

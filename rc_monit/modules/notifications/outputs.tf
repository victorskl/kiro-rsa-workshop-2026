# ---------------------------------------------------------------------------
# modules/notifications/outputs.tf
# ---------------------------------------------------------------------------

output "sns_topic_arn" {
  description = "ARN of the SNS topic that receives CloudWatch alarm notifications."
  value       = aws_sns_topic.alarms.arn
}

output "sns_topic_name" {
  description = "Name of the SNS alarms topic."
  value       = aws_sns_topic.alarms.name
}

output "lambda_function_name" {
  description = "Name of the Slack notifier Lambda function."
  value       = aws_lambda_function.slack_notifier.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Slack notifier Lambda function."
  value       = aws_lambda_function.slack_notifier.arn
}

output "slack_webhook_secret_arn" {
  description = "ARN of the Secrets Manager secret holding the Slack webhook URL."
  value       = aws_secretsmanager_secret.slack_webhook.arn
}

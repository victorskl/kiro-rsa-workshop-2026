# ---------------------------------------------------------------------------
# modules/cost_harvester/outputs.tf
# ---------------------------------------------------------------------------

output "lambda_function_name" {
  description = "Name of the cost harvester Lambda function."
  value       = aws_lambda_function.cost_harvester.function_name
}

output "lambda_function_arn" {
  description = "ARN of the cost harvester Lambda function."
  value       = aws_lambda_function.cost_harvester.arn
}

output "schedule_rule_name" {
  description = "Name of the EventBridge rule that triggers the Lambda."
  value       = aws_cloudwatch_event_rule.schedule.name
}

# ---------------------------------------------------------------------------
# modules/spot_tracker/outputs.tf
# ---------------------------------------------------------------------------

output "lambda_function_name" {
  description = "Name of the spot tracker Lambda function."
  value       = aws_lambda_function.spot_tracker.function_name
}

output "lambda_function_arn" {
  description = "ARN of the spot tracker Lambda function."
  value       = aws_lambda_function.spot_tracker.arn
}

output "event_rule_name" {
  description = "Name of the EventBridge rule that triggers on spot interruptions."
  value       = aws_cloudwatch_event_rule.spot_interruption.name
}

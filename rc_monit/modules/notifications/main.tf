# ---------------------------------------------------------------------------
# modules/notifications/main.tf
#
# Deploys:
#   - SNS topic (shared alarm sink)
#   - Optional email subscriptions
#   - Slack formatter Lambda (reads webhook URL from Secrets Manager)
#   - SNS → Lambda subscription
#   - Secrets Manager secret placeholder for the Slack webhook URL
# ---------------------------------------------------------------------------

locals {
  function_name = "research-slack-notifier"

  # Construct the dashboard URL from name + region if not explicitly provided.
  dashboard_url = var.dashboard_url != "" ? var.dashboard_url : (
    "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${var.dashboard_name}"
  )
}

# ── SNS topic ──────────────────────────────────────────────────────────────

resource "aws_sns_topic" "alarms" {
  name = "research-computing-alarms"
  tags = var.tags
}

# Optional email subscriptions
resource "aws_sns_topic_subscription" "email" {
  for_each = toset(var.alarm_email_addresses)

  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = each.key
}

# ── Secrets Manager — Slack webhook placeholder ───────────────────────────
#
# The secret is created with a placeholder value.
# After deploying, populate it via the AWS console or CLI:
#
#   aws secretsmanager put-secret-value \
#     --secret-id research-monitoring/slack-webhook \
#     --secret-string '{"webhook_url":"https://hooks.slack.com/services/..."}'

resource "aws_secretsmanager_secret" "slack_webhook" {
  name                    = var.slack_webhook_secret_name
  description             = "Slack incoming webhook URL for research computing alarm notifications"
  recovery_window_in_days = 7
  tags                    = var.tags
}

resource "aws_secretsmanager_secret_version" "slack_webhook_placeholder" {
  secret_id     = aws_secretsmanager_secret.slack_webhook.id
  secret_string = jsonencode({ webhook_url = "REPLACE_ME" })

  # Prevent Terraform from overwriting a real webhook URL on subsequent applies.
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# ── Lambda package ─────────────────────────────────────────────────────────

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/lambda/slack_notifier.zip"
}

# ── IAM role ───────────────────────────────────────────────────────────────

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${local.function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags               = var.tags
}

data "aws_iam_policy_document" "lambda_policy" {
  # Secrets Manager — read the Slack webhook URL only
  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [aws_secretsmanager_secret.slack_webhook.arn]
  }

  # CloudWatch Logs — write Lambda logs
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:*:*:log-group:/aws/lambda/${local.function_name}:*"]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "${local.function_name}-policy"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_policy.json
}

# ── CloudWatch Log Group ───────────────────────────────────────────────────

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 30
  tags              = var.tags
}

# ── Lambda function ────────────────────────────────────────────────────────

resource "aws_lambda_function" "slack_notifier" {
  function_name    = local.function_name
  role             = aws_iam_role.lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 30
  memory_size      = 128

  environment {
    variables = {
      SLACK_SECRET_NAME = var.slack_webhook_secret_name
      DASHBOARD_URL     = local.dashboard_url
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda]

  tags = var.tags
}

# ── SNS → Lambda subscription ──────────────────────────────────────────────

resource "aws_lambda_permission" "allow_sns" {
  statement_id  = "AllowExecutionFromSNS"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.slack_notifier.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.alarms.arn
}

resource "aws_sns_topic_subscription" "lambda" {
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.slack_notifier.arn
}

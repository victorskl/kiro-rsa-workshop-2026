# ---------------------------------------------------------------------------
# modules/cost_harvester/main.tf
#
# Packages the cost harvester Lambda and deploys it with:
#   - An IAM role with least-privilege permissions
#   - An EventBridge rule that triggers every 6 hours
#   - A CloudWatch log group for Lambda output
# ---------------------------------------------------------------------------

locals {
  function_name = "research-cost-harvester"
}

# ── Lambda package ─────────────────────────────────────────────────────────

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/lambda/cost_harvester.zip"
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
  # Cost Explorer — read-only cost and usage data
  statement {
    effect    = "Allow"
    actions   = ["ce:GetCostAndUsage"]
    resources = ["*"]
  }

  # CloudWatch — publish custom metrics only
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["ResearchComputing/Costs"]
    }
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

resource "aws_lambda_function" "cost_harvester" {
  function_name    = local.function_name
  role             = aws_iam_role.lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 300 # Cost Explorer calls can be slow for large accounts
  memory_size      = 256

  environment {
    variables = {
      PROJECTS = join(",", var.research_projects)
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda]

  tags = var.tags
}

# ── EventBridge schedule (every 6 hours) ──────────────────────────────────

resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "${local.function_name}-schedule"
  description         = "Trigger cost harvester Lambda every 6 hours"
  schedule_expression = "rate(6 hours)"
  tags                = var.tags
}

resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "cost-harvester-lambda"
  arn       = aws_lambda_function.cost_harvester.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cost_harvester.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.schedule.arn
}

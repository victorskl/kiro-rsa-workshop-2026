---
name: add-lambda
description: Add a new Lambda-based metric collector to the monitoring stack. Use when a new data source needs to be harvested and published as CloudWatch custom metrics.
---

## Checklist

- [ ] `modules/<name>/lambda/handler.py` — single file, standard handler signature
- [ ] `modules/<name>/lambda/test_handler.py` — pytest, boto3 stubbed via sys.modules injection
- [ ] `modules/<name>/main.tf` — archive_file, IAM role, Lambda, CloudWatch log group
- [ ] `modules/<name>/variables.tf` — at minimum: `tags` variable
- [ ] `modules/<name>/outputs.tf` — expose `lambda_function_name` and `lambda_function_arn`
- [ ] Module call added to root `main.tf`
- [ ] Lambda name added to root `outputs.tf`

## Handler template

```python
"""modules/<name>/lambda/handler.py"""
from __future__ import annotations
import logging, os
from typing import Any
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def _get_cw_client(region: str) -> Any:
    return boto3.client("cloudwatch", region_name=region)

def handler(event: dict, context: Any) -> dict:
    region = os.environ.get("AWS_REGION", "us-east-1")
    cw = _get_cw_client(region)
    # ... collect and publish metrics ...
    cw.put_metric_data(
        Namespace="ResearchComputing/Costs",  # or ResearchComputing/Spot
        MetricData=[{ "MetricName": "...", "Value": 0.0, "Unit": "None" }],
    )
    return {"statusCode": 200, "body": "ok"}
```

## Terraform template

```hcl
# modules/<name>/main.tf
locals { function_name = "research-<name>" }

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda/handler.py"
  output_path = "${path.module}/lambda/<name>.zip"
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals { type = "Service"; identifiers = ["lambda.amazonaws.com"] }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${local.function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags               = var.tags
}

data "aws_iam_policy_document" "lambda_policy" {
  statement {
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["ResearchComputing/Costs"]  # narrow to exact namespace
    }
  }
  statement {
    effect    = "Allow"
    actions   = ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:log-group:/aws/lambda/${local.function_name}:*"]
  }
}

resource "aws_iam_role_policy" "lambda" {
  name   = "${local.function_name}-policy"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.lambda_policy.json
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 30
  tags              = var.tags
}

resource "aws_lambda_function" "main" {
  function_name    = local.function_name
  role             = aws_iam_role.lambda.arn
  handler          = "handler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 300
  memory_size      = 256
  depends_on       = [aws_cloudwatch_log_group.lambda]
  tags             = var.tags
}
```

## IAM permissions reference

| Action needed | Permission | Condition |
|---|---|---|
| Publish cost metrics | `cloudwatch:PutMetricData` | `cloudwatch:namespace = ResearchComputing/Costs` |
| Publish spot metrics | `cloudwatch:PutMetricData` | `cloudwatch:namespace = ResearchComputing/Spot` |
| Read Cost Explorer | `ce:GetCostAndUsage` | none (global service) |
| Read EC2 tags | `ec2:DescribeInstances` | none |
| Read Secrets Manager | `secretsmanager:GetSecretValue` | resource = secret ARN |

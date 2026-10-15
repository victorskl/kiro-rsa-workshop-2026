"""
notifications/handler.py

Receives CloudWatch alarm notifications from SNS, formats them into a rich
Slack message, and posts to an incoming webhook URL stored in AWS Secrets
Manager.

Environment variables (injected by Terraform):
  SLACK_SECRET_NAME  – Secrets Manager secret name containing the webhook URL
  DASHBOARD_URL      – Direct link to the CloudWatch dashboard (for message CTA)
  AWS_REGION         – Region (auto-set by Lambda runtime)
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_webhook_url_cache: str | None = None


def _get_webhook_url(secret_name: str, region: str) -> str:
    """
    Fetch the Slack incoming webhook URL from Secrets Manager.
    Cached in-process to avoid redundant API calls on warm invocations.
    """
    global _webhook_url_cache
    if _webhook_url_cache:
        return _webhook_url_cache

    client = boto3.client("secretsmanager", region_name=region)
    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = response.get("SecretString", "")
        # Secret may be a plain URL string or a JSON object {"webhook_url": "..."}
        try:
            parsed = json.loads(secret)
            url = parsed.get("webhook_url", secret)
        except json.JSONDecodeError:
            url = secret.strip()

        _webhook_url_cache = url
        return url
    except ClientError as exc:
        logger.error("Failed to retrieve Slack webhook from Secrets Manager: %s", exc)
        raise


def _parse_alarm(sns_message: str) -> dict:
    """
    Parse the CloudWatch alarm JSON payload embedded in the SNS message body.
    Returns a dict with fields: alarm_name, state, reason, metric, threshold,
    current_value, project, region.
    """
    try:
        alarm = json.loads(sns_message)
    except json.JSONDecodeError:
        logger.warning("Could not parse SNS message as JSON: %s", sns_message[:200])
        return {"alarm_name": "Unknown", "state": "UNKNOWN", "reason": sns_message}

    # Extract Project dimension from trigger dimensions if present
    trigger = alarm.get("Trigger", {})
    dimensions = trigger.get("Dimensions", [])
    project = next(
        (d["value"] for d in dimensions if d.get("name") == "Project"),
        None,
    )

    # Try to extract current metric value from the state reason data
    reason_data_str = alarm.get("NewStateReasonData", "{}")
    try:
        reason_data = json.loads(reason_data_str)
        recent_datapoints = reason_data.get("recentDatapoints", [])
        current_value = recent_datapoints[-1] if recent_datapoints else None
    except (json.JSONDecodeError, IndexError):
        current_value = None

    return {
        "alarm_name":    alarm.get("AlarmName", "Unknown"),
        "state":         alarm.get("NewStateValue", "UNKNOWN"),
        "previous_state": alarm.get("OldStateValue", "UNKNOWN"),
        "reason":        alarm.get("NewStateReason", ""),
        "metric":        trigger.get("MetricName", ""),
        "namespace":     trigger.get("Namespace", ""),
        "threshold":     trigger.get("Threshold"),
        "current_value": current_value,
        "project":       project,
        "region":        alarm.get("Region", ""),
        "account_id":    alarm.get("AWSAccountId", ""),
    }


def _build_slack_message(alarm: dict, dashboard_url: str) -> dict:
    """Build a Slack Block Kit message payload from parsed alarm data."""
    state = alarm["state"]

    # Emoji and colour by state
    if state == "ALARM":
        emoji = "🚨"
        color = "#E01E5A"  # red
    elif state == "OK":
        emoji = "✅"
        color = "#2EB67D"  # green
    else:
        emoji = "⚠️"
        color = "#ECB22E"  # yellow

    title = f"{emoji} *{alarm['alarm_name']}* — `{state}`"

    fields = []
    if alarm.get("project"):
        fields.append({"type": "mrkdwn", "text": f"*Project:*\n{alarm['project']}"})
    if alarm.get("metric"):
        fields.append({"type": "mrkdwn", "text": f"*Metric:*\n{alarm['metric']}"})
    if alarm.get("threshold") is not None:
        fields.append({"type": "mrkdwn", "text": f"*Threshold:*\n{alarm['threshold']}"})
    if alarm.get("current_value") is not None:
        fields.append({"type": "mrkdwn", "text": f"*Current Value:*\n{alarm['current_value']:.2f}"})
    if alarm.get("region"):
        fields.append({"type": "mrkdwn", "text": f"*Region:*\n{alarm['region']}"})

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": title}},
    ]

    if fields:
        blocks.append({"type": "section", "fields": fields[:10]})  # Slack max 10 fields

    if alarm.get("reason"):
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Reason:*\n{alarm['reason'][:400]}"},
        })

    if dashboard_url:
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Dashboard"},
                    "url": dashboard_url,
                    "style": "primary",
                }
            ],
        })

    return {
        "attachments": [
            {
                "color": color,
                "blocks": blocks,
            }
        ]
    }


def _post_to_slack(webhook_url: str, payload: dict) -> None:
    """POST the Slack message payload to the incoming webhook URL."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8")
        status = resp.status
        if status != 200:
            raise RuntimeError(f"Slack webhook returned HTTP {status}: {body}")
        logger.info("Slack notification delivered (HTTP %d)", status)


def handler(event: dict, context: Any) -> dict:
    """Lambda entry point — triggered by SNS subscription."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    secret_name = os.environ.get("SLACK_SECRET_NAME", "research-monitoring/slack-webhook")
    dashboard_url = os.environ.get("DASHBOARD_URL", "")

    records = event.get("Records", [])
    if not records:
        logger.warning("No records in event: %s", event)
        return {"statusCode": 200, "body": "No records to process"}

    webhook_url = _get_webhook_url(secret_name, region)
    errors = []

    for record in records:
        sns_message = record.get("Sns", {}).get("Message", "")
        try:
            alarm = _parse_alarm(sns_message)
            payload = _build_slack_message(alarm, dashboard_url)
            _post_to_slack(webhook_url, payload)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to deliver Slack notification: %s", exc)
            errors.append(str(exc))

    if errors:
        return {"statusCode": 500, "body": json.dumps({"errors": errors})}

    return {"statusCode": 200, "body": json.dumps({"delivered": len(records)})}

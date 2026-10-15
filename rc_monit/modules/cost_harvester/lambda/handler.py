"""
cost_harvester/handler.py

Pulls daily cost-by-tag data from AWS Cost Explorer and publishes custom
CloudWatch metrics to the ResearchComputing/Costs namespace.

Metric dimensions published per record:
  - Project   → DailySpend (USD)
  - Researcher → DailySpend (USD)

Environment variables (injected by Terraform):
  AWS_REGION          – target CloudWatch region
  PROJECTS            – comma-separated list of expected project names (for logging)
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date, timedelta
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

NAMESPACE = "ResearchComputing/Costs"
METRIC_NAME = "DailySpend"
UNIT = "None"  # CloudWatch has no USD unit; we store raw float and label axes


def _get_cost_client() -> Any:
    return boto3.client("ce", region_name="us-east-1")  # CE is global; always us-east-1


def _get_cw_client(region: str) -> Any:
    return boto3.client("cloudwatch", region_name=region)


def _date_range() -> tuple[str, str]:
    """Return (start, end) for yesterday as Cost Explorer date strings."""
    today = date.today()
    yesterday = today - timedelta(days=1)
    return yesterday.isoformat(), today.isoformat()


def _query_costs_by_tag(ce_client: Any, tag_key: str, start: str, end: str) -> list[dict]:
    """
    Call GetCostAndUsage grouped by a single tag key.
    Returns a list of {tag_value, amount_usd} dicts.
    """
    response = ce_client.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "TAG", "Key": tag_key}],
    )

    results = []
    for time_period in response.get("ResultsByTime", []):
        for group in time_period.get("Groups", []):
            # Keys look like ["Project$genome-seq"] — strip the prefix.
            raw_key = group["Keys"][0]
            tag_value = raw_key.split("$", 1)[-1] if "$" in raw_key else raw_key
            if not tag_value:
                tag_value = "__untagged__"
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            results.append({"tag_value": tag_value, "amount_usd": amount})

    return results


def _build_metric_data(tag_key: str, records: list[dict]) -> list[dict]:
    """Convert cost records into CloudWatch PutMetricData MetricData entries."""
    metric_data = []
    for record in records:
        metric_data.append(
            {
                "MetricName": METRIC_NAME,
                "Dimensions": [{"Name": tag_key, "Value": record["tag_value"]}],
                "Value": record["amount_usd"],
                "Unit": UNIT,
            }
        )
    return metric_data


def _publish_metrics(cw_client: Any, metric_data: list[dict]) -> None:
    """
    Publish metrics in batches of 20 (CloudWatch PutMetricData limit is 1000
    metrics per call, but 20 keeps payloads small and easy to reason about).
    """
    batch_size = 20
    for i in range(0, len(metric_data), batch_size):
        batch = metric_data[i : i + batch_size]
        cw_client.put_metric_data(Namespace=NAMESPACE, MetricData=batch)
        logger.info("Published %d metrics to %s", len(batch), NAMESPACE)


def handler(event: dict, context: Any) -> dict:
    """Lambda entry point — called by EventBridge on a schedule."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    start, end = _date_range()
    logger.info("Harvesting costs for %s → %s", start, end)

    ce = _get_cost_client()
    cw = _get_cw_client(region)

    all_metrics: list[dict] = []

    for tag_key in ("Project", "Researcher"):
        try:
            records = _query_costs_by_tag(ce, tag_key, start, end)
            logger.info("Tag=%s: %d records fetched", tag_key, len(records))
            all_metrics.extend(_build_metric_data(tag_key, records))
        except ClientError as exc:
            logger.error("Failed to query costs for tag %s: %s", tag_key, exc)
            raise

    if all_metrics:
        _publish_metrics(cw, all_metrics)
    else:
        logger.warning("No cost data returned for %s → %s", start, end)

    return {"statusCode": 200, "body": json.dumps({"metrics_published": len(all_metrics)})}

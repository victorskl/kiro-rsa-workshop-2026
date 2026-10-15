"""
spot_tracker/handler.py

Handles EC2 Spot Instance Interruption Warning events from EventBridge.
For each event, looks up the Project tag on the interrupted instance and
publishes a SpotInterruption count metric to ResearchComputing/Spot.

EventBridge event shape (detail-type: "EC2 Spot Instance Interruption Warning"):
{
  "version": "0",
  "id": "...",
  "detail-type": "EC2 Spot Instance Interruption Warning",
  "source": "aws.ec2",
  "account": "123456789012",
  "time": "2026-10-15T00:00:00Z",
  "region": "us-east-1",
  "detail": {
    "instance-id": "i-0abc1234",
    "instance-action": "terminate"
  }
}
"""

from __future__ import annotations

import logging
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

NAMESPACE = "ResearchComputing/Spot"
METRIC_NAME = "SpotInterruption"
UNTAGGED_PROJECT = "__untagged__"


def _get_ec2_client(region: str) -> Any:
    return boto3.client("ec2", region_name=region)


def _get_cw_client(region: str) -> Any:
    return boto3.client("cloudwatch", region_name=region)


def _get_project_tag(ec2_client: Any, instance_id: str) -> str:
    """
    Fetch the Project tag value for an EC2 instance.
    Returns UNTAGGED_PROJECT if the tag is absent or the instance is not found.
    """
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        reservations = response.get("Reservations", [])
        if not reservations:
            logger.warning("Instance %s not found", instance_id)
            return UNTAGGED_PROJECT

        tags = reservations[0]["Instances"][0].get("Tags", [])
        for tag in tags:
            if tag["Key"] == "Project":
                return tag["Value"]

        logger.info("No Project tag on instance %s", instance_id)
        return UNTAGGED_PROJECT

    except ClientError as exc:
        logger.error("Failed to describe instance %s: %s", instance_id, exc)
        return UNTAGGED_PROJECT


def _publish_interruption(cw_client: Any, project: str, instance_id: str) -> None:
    """Publish a SpotInterruption count metric for the given project."""
    cw_client.put_metric_data(
        Namespace=NAMESPACE,
        MetricData=[
            {
                "MetricName": METRIC_NAME,
                "Dimensions": [
                    {"Name": "Project", "Value": project},
                    {"Name": "InstanceId", "Value": instance_id},
                ],
                "Value": 1,
                "Unit": "Count",
            }
        ],
    )
    logger.info(
        "Published SpotInterruption metric: project=%s instance=%s",
        project,
        instance_id,
    )


def handler(event: dict, context: Any) -> dict:
    """Lambda entry point — called by EventBridge on spot interruption events."""
    region = event.get("region") or os.environ.get("AWS_REGION", "us-east-1")
    detail = event.get("detail", {})
    instance_id = detail.get("instance-id")

    if not instance_id:
        logger.error("No instance-id in event detail: %s", event)
        return {"statusCode": 400, "body": "Missing instance-id in event"}

    logger.info("Spot interruption for instance %s in region %s", instance_id, region)

    ec2 = _get_ec2_client(region)
    cw = _get_cw_client(region)

    project = _get_project_tag(ec2, instance_id)
    _publish_interruption(cw, project, instance_id)

    return {"statusCode": 200, "body": f"Published interruption for {instance_id} (project={project})"}

"""
test_handler.py — unit tests for spot_tracker/handler.py

Run with:  python -m pytest modules/spot_tracker/lambda/test_handler.py -v
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Minimal boto3 / botocore stubs
# ---------------------------------------------------------------------------

def _ensure_boto3_stub():
    if "boto3" not in sys.modules:
        boto3_mod = types.ModuleType("boto3")
        boto3_mod.client = MagicMock()
        sys.modules["boto3"] = boto3_mod

    if "botocore.exceptions" not in sys.modules:
        botocore_mod = types.ModuleType("botocore")
        exceptions_mod = types.ModuleType("botocore.exceptions")

        class ClientError(Exception):
            def __init__(self, error_response, operation_name):
                self.response = error_response
                self.operation_name = operation_name
                super().__init__(str(error_response))

        exceptions_mod.ClientError = ClientError
        botocore_mod.exceptions = exceptions_mod
        sys.modules["botocore"] = botocore_mod
        sys.modules["botocore.exceptions"] = exceptions_mod


_ensure_boto3_stub()

_handler_path = pathlib.Path(__file__).parent / "handler.py"
_spec = importlib.util.spec_from_file_location("spot_handler", _handler_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_get_project_tag = _mod._get_project_tag
_publish_interruption = _mod._publish_interruption
handler = _mod.handler

# ── Synthetic EventBridge event ────────────────────────────────────────────

SAMPLE_EVENT = {
    "version": "0",
    "id": "abc-123",
    "detail-type": "EC2 Spot Instance Interruption Warning",
    "source": "aws.ec2",
    "account": "123456789012",
    "time": "2026-10-15T00:00:00Z",
    "region": "us-east-1",
    "detail": {
        "instance-id": "i-0abc1234def567890",
        "instance-action": "terminate",
    },
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetProjectTag:
    def _make_ec2_response(self, tags: list[dict]) -> dict:
        return {
            "Reservations": [
                {"Instances": [{"InstanceId": "i-0abc1234", "Tags": tags}]}
            ]
        }

    def test_returns_project_tag_value(self):
        ec2 = MagicMock()
        ec2.describe_instances.return_value = self._make_ec2_response(
            [{"Key": "Project", "Value": "genome-seq"}]
        )
        assert _get_project_tag(ec2, "i-0abc1234") == "genome-seq"

    def test_returns_untagged_when_no_project_tag(self):
        ec2 = MagicMock()
        ec2.describe_instances.return_value = self._make_ec2_response(
            [{"Key": "Team", "Value": "bio"}]
        )
        assert _get_project_tag(ec2, "i-0abc1234") == "__untagged__"

    def test_returns_untagged_when_instance_not_found(self):
        ec2 = MagicMock()
        ec2.describe_instances.return_value = {"Reservations": []}
        assert _get_project_tag(ec2, "i-0abc1234") == "__untagged__"

    def test_returns_untagged_on_client_error(self):
        from botocore.exceptions import ClientError

        ec2 = MagicMock()
        ec2.describe_instances.side_effect = ClientError(
            {"Error": {"Code": "InvalidInstanceID.NotFound", "Message": "not found"}},
            "DescribeInstances",
        )
        assert _get_project_tag(ec2, "i-0abc1234") == "__untagged__"


class TestPublishInterruption:
    def test_publishes_correct_metric(self):
        cw = MagicMock()
        _publish_interruption(cw, "genome-seq", "i-0abc1234")
        cw.put_metric_data.assert_called_once()
        call_kwargs = cw.put_metric_data.call_args[1]
        assert call_kwargs["Namespace"] == "ResearchComputing/Spot"
        metric = call_kwargs["MetricData"][0]
        assert metric["MetricName"] == "SpotInterruption"
        assert metric["Value"] == 1
        assert metric["Unit"] == "Count"
        dims = {d["Name"]: d["Value"] for d in metric["Dimensions"]}
        assert dims["Project"] == "genome-seq"
        assert dims["InstanceId"] == "i-0abc1234"


class TestHandler:
    def test_happy_path(self, monkeypatch):
        ec2_mock = MagicMock()
        cw_mock = MagicMock()
        ec2_mock.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-0abc1234def567890",
                            "Tags": [{"Key": "Project", "Value": "genome-seq"}],
                        }
                    ]
                }
            ]
        }
        monkeypatch.setattr(_mod, "_get_ec2_client", lambda r: ec2_mock)
        monkeypatch.setattr(_mod, "_get_cw_client", lambda r: cw_mock)

        result = handler(SAMPLE_EVENT, None)
        assert result["statusCode"] == 200
        assert "genome-seq" in result["body"]

    def test_missing_instance_id_returns_400(self):
        event = {"detail": {}, "region": "us-east-1"}
        result = handler(event, None)
        assert result["statusCode"] == 400

    def test_untagged_instance_still_publishes(self, monkeypatch):
        ec2_mock = MagicMock()
        cw_mock = MagicMock()
        ec2_mock.describe_instances.return_value = {
            "Reservations": [{"Instances": [{"InstanceId": "i-0abc", "Tags": []}]}]
        }
        monkeypatch.setattr(_mod, "_get_ec2_client", lambda r: ec2_mock)
        monkeypatch.setattr(_mod, "_get_cw_client", lambda r: cw_mock)

        result = handler(SAMPLE_EVENT, None)
        assert result["statusCode"] == 200
        assert "__untagged__" in result["body"]
        cw_mock.put_metric_data.assert_called_once()

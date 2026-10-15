"""
test_handler.py — unit tests for notifications/handler.py

Run with:  python -m pytest modules/notifications/lambda/test_handler.py -v
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

def _ensure_stubs():
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


_ensure_stubs()

_handler_path = pathlib.Path(__file__).parent / "handler.py"
_spec = importlib.util.spec_from_file_location("notifications_handler", _handler_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

_parse_alarm = _mod._parse_alarm
_build_slack_message = _mod._build_slack_message
_post_to_slack = _mod._post_to_slack
handler = _mod.handler


# ---------------------------------------------------------------------------
# Sample payloads
# ---------------------------------------------------------------------------

ALARM_PAYLOAD = json.dumps({
    "AlarmName": "research-cost-spike-genome-seq",
    "NewStateValue": "ALARM",
    "OldStateValue": "OK",
    "NewStateReason": "Threshold Crossed: 1 out of the last 1 datapoints [523.45] was greater than the threshold (500.0).",
    "NewStateReasonData": json.dumps({"recentDatapoints": [523.45]}),
    "AWSAccountId": "123456789012",
    "Region": "us-east-1",
    "Trigger": {
        "MetricName": "DailySpend",
        "Namespace": "ResearchComputing/Costs",
        "Threshold": 500.0,
        "Dimensions": [{"name": "Project", "value": "genome-seq"}],
    },
})

SNS_EVENT = {
    "Records": [
        {
            "Sns": {
                "Message": ALARM_PAYLOAD,
            }
        }
    ]
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestParseAlarm:
    def test_parses_alarm_name(self):
        alarm = _parse_alarm(ALARM_PAYLOAD)
        assert alarm["alarm_name"] == "research-cost-spike-genome-seq"

    def test_parses_state(self):
        alarm = _parse_alarm(ALARM_PAYLOAD)
        assert alarm["state"] == "ALARM"

    def test_parses_project_dimension(self):
        alarm = _parse_alarm(ALARM_PAYLOAD)
        assert alarm["project"] == "genome-seq"

    def test_parses_threshold(self):
        alarm = _parse_alarm(ALARM_PAYLOAD)
        assert alarm["threshold"] == 500.0

    def test_parses_current_value(self):
        alarm = _parse_alarm(ALARM_PAYLOAD)
        assert alarm["current_value"] == pytest.approx(523.45)

    def test_invalid_json_returns_fallback(self):
        alarm = _parse_alarm("not json")
        assert alarm["alarm_name"] == "Unknown"
        assert alarm["state"] == "UNKNOWN"


class TestBuildSlackMessage:
    def test_alarm_state_uses_red_color(self):
        alarm = _parse_alarm(ALARM_PAYLOAD)
        msg = _build_slack_message(alarm, "https://example.com/dashboard")
        assert msg["attachments"][0]["color"] == "#E01E5A"

    def test_ok_state_uses_green_color(self):
        alarm = {**_parse_alarm(ALARM_PAYLOAD), "state": "OK"}
        msg = _build_slack_message(alarm, "")
        assert msg["attachments"][0]["color"] == "#2EB67D"

    def test_message_contains_alarm_name(self):
        alarm = _parse_alarm(ALARM_PAYLOAD)
        msg = _build_slack_message(alarm, "")
        blocks_text = json.dumps(msg)
        assert "research-cost-spike-genome-seq" in blocks_text

    def test_dashboard_button_included_when_url_provided(self):
        alarm = _parse_alarm(ALARM_PAYLOAD)
        msg = _build_slack_message(alarm, "https://example.com/dashboard")
        blocks_text = json.dumps(msg)
        assert "View Dashboard" in blocks_text
        assert "https://example.com/dashboard" in blocks_text

    def test_no_dashboard_button_when_url_empty(self):
        alarm = _parse_alarm(ALARM_PAYLOAD)
        msg = _build_slack_message(alarm, "")
        blocks_text = json.dumps(msg)
        assert "View Dashboard" not in blocks_text


class TestPostToSlack:
    def test_posts_json_payload(self):
        payload = {"text": "test"}
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = b"ok"
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_open.return_value = mock_resp
            _post_to_slack("https://hooks.slack.com/test", payload)
            mock_open.assert_called_once()

    def test_raises_on_non_200(self):
        payload = {"text": "test"}
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.status = 403
            mock_resp.read.return_value = b"forbidden"
            mock_resp.__enter__ = lambda s: s
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_open.return_value = mock_resp
            with pytest.raises(RuntimeError, match="HTTP 403"):
                _post_to_slack("https://hooks.slack.com/test", payload)


class TestHandler:
    def test_happy_path(self, monkeypatch):
        monkeypatch.setenv("SLACK_SECRET_NAME", "test-secret")
        monkeypatch.setenv("DASHBOARD_URL", "https://example.com")
        monkeypatch.setattr(_mod, "_get_webhook_url", lambda s, r: "https://hooks.slack.com/test")
        monkeypatch.setattr(_mod, "_post_to_slack", lambda url, payload: None)

        result = handler(SNS_EVENT, None)
        assert result["statusCode"] == 200

    def test_empty_records(self, monkeypatch):
        result = handler({"Records": []}, None)
        assert result["statusCode"] == 200

    def test_error_in_delivery_returns_500(self, monkeypatch):
        monkeypatch.setenv("SLACK_SECRET_NAME", "test-secret")
        monkeypatch.setattr(_mod, "_get_webhook_url", lambda s, r: "https://hooks.slack.com/test")
        monkeypatch.setattr(_mod, "_post_to_slack", lambda url, payload: (_ for _ in ()).throw(RuntimeError("failed")))

        result = handler(SNS_EVENT, None)
        assert result["statusCode"] == 500

"""
test_handler.py — unit tests for cost_harvester/handler.py

Run with:  python -m pytest modules/cost_harvester/lambda/test_handler.py -v
"""

from __future__ import annotations

import importlib
import sys
import types
from datetime import date, timedelta
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Minimal boto3 stub so the module can be imported without real AWS creds.
# ---------------------------------------------------------------------------

def _make_boto3_stub():
    boto3_mod = types.ModuleType("boto3")
    boto3_mod.client = MagicMock()
    botocore_mod = types.ModuleType("botocore")
    exceptions_mod = types.ModuleType("botocore.exceptions")

    class ClientError(Exception):
        def __init__(self, error_response, operation_name):
            self.response = error_response
            self.operation_name = operation_name
            super().__init__(str(error_response))

    exceptions_mod.ClientError = ClientError
    botocore_mod.exceptions = exceptions_mod
    sys.modules.setdefault("boto3", boto3_mod)
    sys.modules.setdefault("botocore", botocore_mod)
    sys.modules.setdefault("botocore.exceptions", exceptions_mod)
    return boto3_mod


_make_boto3_stub()

# Now safe to import handler
import importlib.util, pathlib

_handler_path = pathlib.Path(__file__).parent / "handler.py"
_spec = importlib.util.spec_from_file_location("handler", _handler_path)
_handler_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_handler_module)

_date_range = _handler_module._date_range
_query_costs_by_tag = _handler_module._query_costs_by_tag
_build_metric_data = _handler_module._build_metric_data
_publish_metrics = _handler_module._publish_metrics
handler = _handler_module.handler


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDateRange:
    def test_returns_yesterday_and_today(self):
        start, end = _date_range()
        today = date.today()
        yesterday = today - timedelta(days=1)
        assert start == yesterday.isoformat()
        assert end == today.isoformat()

    def test_end_is_one_day_after_start(self):
        start, end = _date_range()
        delta = date.fromisoformat(end) - date.fromisoformat(start)
        assert delta.days == 1


class TestQueryCostsByTag:
    def _make_ce_response(self):
        return {
            "ResultsByTime": [
                {
                    "Groups": [
                        {
                            "Keys": ["Project$genome-seq"],
                            "Metrics": {"UnblendedCost": {"Amount": "123.45"}},
                        },
                        {
                            "Keys": ["Project$protein-fold"],
                            "Metrics": {"UnblendedCost": {"Amount": "67.89"}},
                        },
                    ]
                }
            ]
        }

    def test_parses_tag_values(self):
        ce = MagicMock()
        ce.get_cost_and_usage.return_value = self._make_ce_response()
        records = _query_costs_by_tag(ce, "Project", "2026-10-13", "2026-10-14")
        assert len(records) == 2
        assert records[0]["tag_value"] == "genome-seq"
        assert records[0]["amount_usd"] == pytest.approx(123.45)

    def test_untagged_resources_labelled(self):
        ce = MagicMock()
        ce.get_cost_and_usage.return_value = {
            "ResultsByTime": [
                {
                    "Groups": [
                        {
                            "Keys": ["Project$"],
                            "Metrics": {"UnblendedCost": {"Amount": "10.00"}},
                        }
                    ]
                }
            ]
        }
        records = _query_costs_by_tag(ce, "Project", "2026-10-13", "2026-10-14")
        assert records[0]["tag_value"] == "__untagged__"

    def test_empty_result_returns_empty_list(self):
        ce = MagicMock()
        ce.get_cost_and_usage.return_value = {"ResultsByTime": []}
        records = _query_costs_by_tag(ce, "Project", "2026-10-13", "2026-10-14")
        assert records == []


class TestBuildMetricData:
    def test_correct_dimensions(self):
        records = [{"tag_value": "genome-seq", "amount_usd": 99.0}]
        metrics = _build_metric_data("Project", records)
        assert len(metrics) == 1
        assert metrics[0]["MetricName"] == "DailySpend"
        assert metrics[0]["Dimensions"] == [{"Name": "Project", "Value": "genome-seq"}]
        assert metrics[0]["Value"] == pytest.approx(99.0)

    def test_multiple_records(self):
        records = [
            {"tag_value": "genome-seq", "amount_usd": 10.0},
            {"tag_value": "protein-fold", "amount_usd": 20.0},
        ]
        metrics = _build_metric_data("Project", records)
        assert len(metrics) == 2


class TestPublishMetrics:
    def test_batches_correctly(self):
        cw = MagicMock()
        # 45 metrics → should result in 3 calls (20 + 20 + 5)
        metrics = [{"MetricName": "DailySpend", "Value": float(i)} for i in range(45)]
        _publish_metrics(cw, metrics)
        assert cw.put_metric_data.call_count == 3

    def test_empty_metrics_no_call(self):
        cw = MagicMock()
        _publish_metrics(cw, [])
        cw.put_metric_data.assert_not_called()


class TestHandler:
    def _ce_response(self, tag_key: str):
        return {
            "ResultsByTime": [
                {
                    "Groups": [
                        {
                            "Keys": [f"{tag_key}$test-value"],
                            "Metrics": {"UnblendedCost": {"Amount": "50.00"}},
                        }
                    ]
                }
            ]
        }

    def test_handler_publishes_metrics(self, monkeypatch):
        ce_mock = MagicMock()
        cw_mock = MagicMock()
        ce_mock.get_cost_and_usage.side_effect = [
            self._ce_response("Project"),
            self._ce_response("Researcher"),
        ]
        monkeypatch.setattr(_handler_module, "_get_cost_client", lambda: ce_mock)
        monkeypatch.setattr(_handler_module, "_get_cw_client", lambda r: cw_mock)

        result = handler({}, None)
        assert result["statusCode"] == 200
        assert cw_mock.put_metric_data.called

    def test_handler_returns_count(self, monkeypatch):
        import json as _json

        ce_mock = MagicMock()
        cw_mock = MagicMock()
        ce_mock.get_cost_and_usage.side_effect = [
            self._ce_response("Project"),
            self._ce_response("Researcher"),
        ]
        monkeypatch.setattr(_handler_module, "_get_cost_client", lambda: ce_mock)
        monkeypatch.setattr(_handler_module, "_get_cw_client", lambda r: cw_mock)

        result = handler({}, None)
        body = _json.loads(result["body"])
        assert body["metrics_published"] == 2  # 1 per tag key

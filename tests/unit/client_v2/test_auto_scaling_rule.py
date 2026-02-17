"""Unit tests for AutoScalingRuleClient (SDK v2)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.auto_scaling_rule import AutoScalingRuleClient
from ai.backend.common.dto.manager.auto_scaling_rule import (
    CreateAutoScalingRuleRequest,
    CreateAutoScalingRuleResponse,
    DeleteAutoScalingRuleRequest,
    DeleteAutoScalingRuleResponse,
    GetAutoScalingRuleResponse,
    SearchAutoScalingRulesRequest,
    SearchAutoScalingRulesResponse,
    UpdateAutoScalingRuleRequest,
    UpdateAutoScalingRuleResponse,
)
from ai.backend.common.types import AutoScalingMetricSource

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_request_session(resp: AsyncMock) -> MagicMock:
    """Build a mock aiohttp session whose ``request()`` returns *resp*."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _json_response(data: dict[str, Any], *, status: int = 200) -> AsyncMock:
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=data)
    return resp


def _make_auto_scaling_rule_client(mock_session: MagicMock) -> AutoScalingRuleClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return AutoScalingRuleClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    """Return (method, url, json_body) from the last ``session.request()`` call."""
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

_SAMPLE_RULE_ID = uuid4()
_SAMPLE_DEPLOYMENT_ID = uuid4()

_SAMPLE_RULE_DTO: dict[str, Any] = {
    "id": str(_SAMPLE_RULE_ID),
    "model_deployment_id": str(_SAMPLE_DEPLOYMENT_ID),
    "metric_source": "kernel",
    "metric_name": "cpu_util",
    "min_threshold": "0.2",
    "max_threshold": "0.8",
    "step_size": 1,
    "time_window": 60,
    "min_replicas": 1,
    "max_replicas": 5,
    "created_at": "2025-01-01T00:00:00",
    "last_triggered_at": "2025-01-01T00:00:00",
}


# ---------------------------------------------------------------------------
# AutoScalingRule CRUD
# ---------------------------------------------------------------------------


class TestAutoScalingRuleCRUD:
    @pytest.mark.asyncio
    async def test_create(self) -> None:
        resp = _json_response({"auto_scaling_rule": _SAMPLE_RULE_DTO})
        mock_session = _make_request_session(resp)
        client = _make_auto_scaling_rule_client(mock_session)

        request = CreateAutoScalingRuleRequest(
            model_deployment_id=_SAMPLE_DEPLOYMENT_ID,
            metric_source=AutoScalingMetricSource.KERNEL,
            metric_name="cpu_util",
            min_threshold=Decimal("0.2"),
            max_threshold=Decimal("0.8"),
            step_size=1,
            time_window=60,
            min_replicas=1,
            max_replicas=5,
        )

        result = await client.create(request)

        assert isinstance(result, CreateAutoScalingRuleResponse)
        assert result.auto_scaling_rule.metric_name == "cpu_util"
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/auto-scaling-rules")
        assert body is not None
        assert body["metric_name"] == "cpu_util"

    @pytest.mark.asyncio
    async def test_get(self) -> None:
        resp = _json_response({"auto_scaling_rule": _SAMPLE_RULE_DTO})
        mock_session = _make_request_session(resp)
        client = _make_auto_scaling_rule_client(mock_session)

        result = await client.get(_SAMPLE_RULE_ID)

        assert isinstance(result, GetAutoScalingRuleResponse)
        assert result.auto_scaling_rule.id == _SAMPLE_RULE_ID
        method, url, _ = _last_request_call(mock_session)
        assert method == "GET"
        assert str(_SAMPLE_RULE_ID) in url

    @pytest.mark.asyncio
    async def test_search(self) -> None:
        resp = _json_response({
            "auto_scaling_rules": [_SAMPLE_RULE_DTO],
            "pagination": {"total": 1, "offset": 0, "limit": 50},
        })
        mock_session = _make_request_session(resp)
        client = _make_auto_scaling_rule_client(mock_session)

        result = await client.search(SearchAutoScalingRulesRequest())

        assert isinstance(result, SearchAutoScalingRulesResponse)
        assert len(result.auto_scaling_rules) == 1
        assert result.pagination.total == 1
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/auto-scaling-rules/search")
        assert body is not None

    @pytest.mark.asyncio
    async def test_update(self) -> None:
        updated_dto = {**_SAMPLE_RULE_DTO, "step_size": 2}
        resp = _json_response({"auto_scaling_rule": updated_dto})
        mock_session = _make_request_session(resp)
        client = _make_auto_scaling_rule_client(mock_session)

        result = await client.update(
            _SAMPLE_RULE_ID,
            UpdateAutoScalingRuleRequest(step_size=2),
        )

        assert isinstance(result, UpdateAutoScalingRuleResponse)
        assert result.auto_scaling_rule.step_size == 2
        method, url, body = _last_request_call(mock_session)
        assert method == "PATCH"
        assert str(_SAMPLE_RULE_ID) in url
        assert body is not None
        assert body["step_size"] == 2

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        resp = _json_response({"deleted": True})
        mock_session = _make_request_session(resp)
        client = _make_auto_scaling_rule_client(mock_session)

        result = await client.delete(
            DeleteAutoScalingRuleRequest(rule_id=_SAMPLE_RULE_ID),
        )

        assert isinstance(result, DeleteAutoScalingRuleResponse)
        assert result.deleted is True
        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert url.endswith("/admin/auto-scaling-rules/delete")
        assert body is not None
        assert str(body["rule_id"]) == str(_SAMPLE_RULE_ID)

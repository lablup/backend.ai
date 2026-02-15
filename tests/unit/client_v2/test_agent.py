from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.agent import AgentClient
from ai.backend.common.dto.manager.agent import (
    AgentFilter,
    AgentOrder,
    SearchAgentsRequest,
    SearchAgentsResponse,
)
from ai.backend.common.dto.manager.agent.types import (
    AgentOrderField,
    AgentStatusEnum,
    AgentStatusEnumFilter,
    OrderDirection,
)

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


def _make_request_session(resp: AsyncMock) -> MagicMock:
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


def _make_client(mock_session: MagicMock) -> BackendAIClient:
    return BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)


def _make_agent_client(mock_session: MagicMock) -> AgentClient:
    return AgentClient(_make_client(mock_session))


class TestSearchAgents:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": "agent-001",
                        "status": "ALIVE",
                        "region": "us-east-1",
                        "resource_group": "default",
                        "schedulable": True,
                        "available_slots": {"cpu": "4", "mem": "8G"},
                        "occupied_slots": {"cpu": "2", "mem": "4G"},
                        "addr": "10.0.0.1:6001",
                        "architecture": "x86_64",
                        "version": "24.12.0",
                    },
                ],
                "pagination": {"total": 1, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_agent_client(mock_session)

        request = SearchAgentsRequest()
        result = await client.search_agents(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/agents/search" in str(call_args[0][1])
        assert isinstance(result, SearchAgentsResponse)
        assert len(result.items) == 1
        assert result.items[0].id == "agent-001"
        assert result.items[0].status == "ALIVE"
        assert result.items[0].schedulable is True
        assert result.pagination.total == 1

    @pytest.mark.asyncio
    async def test_with_status_filter(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [],
                "pagination": {"total": 0, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_agent_client(mock_session)

        request = SearchAgentsRequest(
            filter=AgentFilter(
                status=AgentStatusEnumFilter(
                    in_=[AgentStatusEnum.ALIVE, AgentStatusEnum.RESTARTING],
                ),
            ),
        )
        result = await client.search_agents(request)

        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["filter"]["status"]["in_"] == ["ALIVE", "RESTARTING"]
        assert isinstance(result, SearchAgentsResponse)

    @pytest.mark.asyncio
    async def test_with_ordering(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [],
                "pagination": {"total": 0, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_agent_client(mock_session)

        request = SearchAgentsRequest(
            order=[
                AgentOrder(
                    field=AgentOrderField.STATUS,
                    direction=OrderDirection.DESC,
                ),
            ],
            limit=25,
        )
        result = await client.search_agents(request)

        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["order"][0]["field"] == "status"
        assert body["order"][0]["direction"] == "desc"
        assert body["limit"] == 25
        assert isinstance(result, SearchAgentsResponse)

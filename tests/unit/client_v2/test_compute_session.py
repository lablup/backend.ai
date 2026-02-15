from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.compute_session import ComputeSessionClient
from ai.backend.common.dto.manager.compute_session import (
    SearchComputeSessionsRequest,
    SearchComputeSessionsResponse,
)
from ai.backend.common.dto.manager.compute_session.types import (
    ComputeSessionFilter,
    ComputeSessionOrder,
    ComputeSessionOrderField,
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


def _make_compute_session_client(mock_session: MagicMock) -> ComputeSessionClient:
    return ComputeSessionClient(_make_client(mock_session))


class TestSearchComputeSessions:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "name": "my-session",
                        "type": "interactive",
                        "status": "RUNNING",
                        "image": ["cr.backend.ai/stable/python:3.11"],
                        "scaling_group": "default",
                        "resource_slots": {"cpu": "4", "mem": "8G"},
                        "occupied_slots": {"cpu": "2", "mem": "4G"},
                        "created_at": "2025-01-01T00:00:00",
                        "terminated_at": None,
                        "starts_at": "2025-01-01T00:00:00",
                        "containers": [
                            {
                                "id": "22222222-2222-2222-2222-222222222222",
                                "agent_id": "agent-001",
                                "status": "RUNNING",
                                "resource_usage": {"cpu": "50%"},
                            },
                        ],
                    },
                ],
                "pagination": {"total": 1, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_compute_session_client(mock_session)

        request = SearchComputeSessionsRequest()
        result = await client.search_sessions(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/compute-sessions/search" in str(call_args[0][1])
        assert isinstance(result, SearchComputeSessionsResponse)
        assert len(result.items) == 1
        assert result.items[0].name == "my-session"
        assert result.items[0].status == "RUNNING"
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
        client = _make_compute_session_client(mock_session)

        request = SearchComputeSessionsRequest(
            filter=ComputeSessionFilter(
                status=["RUNNING", "PREPARING"],
            ),
        )
        result = await client.search_sessions(request)

        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["filter"]["status"] == ["RUNNING", "PREPARING"]
        assert isinstance(result, SearchComputeSessionsResponse)

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
        client = _make_compute_session_client(mock_session)

        request = SearchComputeSessionsRequest(
            order=[
                ComputeSessionOrder(
                    field=ComputeSessionOrderField.CREATED_AT,
                    direction=OrderDirection.ASC,
                ),
            ],
            limit=20,
            offset=10,
        )
        result = await client.search_sessions(request)

        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["order"][0]["field"] == "created_at"
        assert body["order"][0]["direction"] == "asc"
        assert body["limit"] == 20
        assert body["offset"] == 10
        assert isinstance(result, SearchComputeSessionsResponse)

    @pytest.mark.asyncio
    async def test_nested_containers(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": "33333333-3333-3333-3333-333333333333",
                        "name": "multi-container",
                        "type": "batch",
                        "status": "RUNNING",
                        "image": None,
                        "scaling_group": None,
                        "resource_slots": None,
                        "occupied_slots": None,
                        "created_at": "2025-01-01T00:00:00",
                        "terminated_at": None,
                        "starts_at": None,
                        "containers": [
                            {
                                "id": "44444444-4444-4444-4444-444444444444",
                                "agent_id": "agent-001",
                                "status": "RUNNING",
                                "resource_usage": None,
                            },
                            {
                                "id": "55555555-5555-5555-5555-555555555555",
                                "agent_id": "agent-002",
                                "status": "PREPARING",
                                "resource_usage": None,
                            },
                        ],
                    },
                ],
                "pagination": {"total": 1, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_compute_session_client(mock_session)

        request = SearchComputeSessionsRequest()
        result = await client.search_sessions(request)

        assert len(result.items) == 1
        session = result.items[0]
        assert len(session.containers) == 2
        assert session.containers[0].agent_id == "agent-001"
        assert session.containers[1].status == "PREPARING"

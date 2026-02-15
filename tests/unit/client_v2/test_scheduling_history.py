from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.scheduling_history import SchedulingHistoryClient
from ai.backend.common.dto.manager.scheduling_history import (
    ListDeploymentHistoryResponse,
    ListRouteHistoryResponse,
    ListSessionHistoryResponse,
    SearchDeploymentHistoryRequest,
    SearchRouteHistoryRequest,
    SearchSessionHistoryRequest,
)
from ai.backend.common.dto.manager.scheduling_history.types import (
    DeploymentHistoryFilter,
    DeploymentHistoryOrder,
    DeploymentHistoryOrderField,
    OrderDirection,
    RouteHistoryFilter,
    SchedulingResultType,
    SessionHistoryFilter,
    SessionHistoryOrder,
    SessionHistoryOrderField,
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


def _make_scheduling_history_client(mock_session: MagicMock) -> SchedulingHistoryClient:
    return SchedulingHistoryClient(_make_client(mock_session))


class TestSearchSessionHistory:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": "11111111-1111-1111-1111-111111111111",
                        "session_id": "22222222-2222-2222-2222-222222222222",
                        "phase": "CREATING",
                        "from_status": None,
                        "to_status": "PREPARING",
                        "result": "SUCCESS",
                        "error_code": None,
                        "message": None,
                        "sub_steps": [],
                        "attempts": 1,
                        "created_at": "2025-01-01T00:00:00",
                        "updated_at": "2025-01-01T00:00:01",
                    },
                ],
                "pagination": {"total": 1, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_scheduling_history_client(mock_session)

        request = SearchSessionHistoryRequest()
        result = await client.search_session_history(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/scheduling-history/sessions/search" in str(call_args[0][1])
        assert isinstance(result, ListSessionHistoryResponse)
        assert len(result.items) == 1
        assert result.items[0].result == "SUCCESS"
        assert result.pagination.total == 1

    @pytest.mark.asyncio
    async def test_with_filters(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [],
                "pagination": {"total": 0, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_scheduling_history_client(mock_session)

        request = SearchSessionHistoryRequest(
            filter=SessionHistoryFilter(
                result=[SchedulingResultType.FAILURE],
            ),
            limit=10,
            offset=0,
        )
        result = await client.search_session_history(request)

        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["filter"]["result"] == ["FAILURE"]
        assert body["limit"] == 10
        assert isinstance(result, ListSessionHistoryResponse)

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
        client = _make_scheduling_history_client(mock_session)

        request = SearchSessionHistoryRequest(
            order=[
                SessionHistoryOrder(
                    field=SessionHistoryOrderField.CREATED_AT,
                    direction=OrderDirection.ASC,
                ),
            ],
        )
        result = await client.search_session_history(request)

        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["order"][0]["field"] == "created_at"
        assert body["order"][0]["direction"] == "asc"
        assert isinstance(result, ListSessionHistoryResponse)


class TestSearchDeploymentHistory:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": "33333333-3333-3333-3333-333333333333",
                        "deployment_id": "44444444-4444-4444-4444-444444444444",
                        "phase": "SCALING",
                        "from_status": "RUNNING",
                        "to_status": "RUNNING",
                        "result": "SUCCESS",
                        "error_code": None,
                        "message": None,
                        "sub_steps": [],
                        "attempts": 2,
                        "created_at": "2025-01-01T00:00:00",
                        "updated_at": "2025-01-01T00:00:01",
                    },
                ],
                "pagination": {"total": 1, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_scheduling_history_client(mock_session)

        request = SearchDeploymentHistoryRequest()
        result = await client.search_deployment_history(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/scheduling-history/deployments/search" in str(call_args[0][1])
        assert isinstance(result, ListDeploymentHistoryResponse)
        assert len(result.items) == 1
        assert result.items[0].attempts == 2

    @pytest.mark.asyncio
    async def test_with_filters(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [],
                "pagination": {"total": 0, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_scheduling_history_client(mock_session)

        request = SearchDeploymentHistoryRequest(
            filter=DeploymentHistoryFilter(
                result=[SchedulingResultType.SUCCESS],
            ),
            order=[
                DeploymentHistoryOrder(
                    field=DeploymentHistoryOrderField.UPDATED_AT,
                    direction=OrderDirection.DESC,
                ),
            ],
        )
        result = await client.search_deployment_history(request)

        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["filter"]["result"] == ["SUCCESS"]
        assert isinstance(result, ListDeploymentHistoryResponse)


class TestSearchRouteHistory:
    @pytest.mark.asyncio
    async def test_happy_path(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [
                    {
                        "id": "55555555-5555-5555-5555-555555555555",
                        "route_id": "66666666-6666-6666-6666-666666666666",
                        "deployment_id": "77777777-7777-7777-7777-777777777777",
                        "phase": "CREATING",
                        "from_status": None,
                        "to_status": "PROVISIONING",
                        "result": "SUCCESS",
                        "error_code": None,
                        "message": None,
                        "sub_steps": [],
                        "attempts": 1,
                        "created_at": "2025-01-01T00:00:00",
                        "updated_at": "2025-01-01T00:00:01",
                    },
                ],
                "pagination": {"total": 1, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_scheduling_history_client(mock_session)

        request = SearchRouteHistoryRequest()
        result = await client.search_route_history(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/scheduling-history/routes/search" in str(call_args[0][1])
        assert isinstance(result, ListRouteHistoryResponse)
        assert len(result.items) == 1
        assert str(result.items[0].route_id) == "66666666-6666-6666-6666-666666666666"

    @pytest.mark.asyncio
    async def test_with_filters(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "items": [],
                "pagination": {"total": 0, "offset": 0, "limit": 50},
            }
        )
        mock_session = _make_request_session(mock_resp)
        client = _make_scheduling_history_client(mock_session)

        request = SearchRouteHistoryRequest(
            filter=RouteHistoryFilter(
                result=[SchedulingResultType.STALE],
            ),
        )
        result = await client.search_route_history(request)

        call_kwargs = mock_session.request.call_args.kwargs
        body = call_kwargs["json"]
        assert body["filter"]["result"] == ["STALE"]
        assert isinstance(result, ListRouteHistoryResponse)

from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.quota_scope import QuotaScopeClient
from ai.backend.common.dto.manager.quota_scope.request import (
    SearchQuotaScopesRequest,
    SetQuotaRequest,
    UnsetQuotaRequest,
)
from ai.backend.common.dto.manager.quota_scope.response import (
    GetQuotaScopeResponse,
    SearchQuotaScopesResponse,
    SetQuotaResponse,
    UnsetQuotaResponse,
)

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))

_QUOTA_SCOPE_PAYLOAD = {
    "quota_scope_id": "user:test-user-uuid",
    "storage_host_name": "local:volume1",
    "usage_bytes": 1048576,
    "usage_count": 10,
    "hard_limit_bytes": 10737418240,
}


def _make_client(
    mock_session: MagicMock | None = None,
    config: ClientConfig | None = None,
) -> BackendAIClient:
    return BackendAIClient(
        config or _DEFAULT_CONFIG,
        MockAuth(),
        mock_session or MagicMock(),
    )


def _make_request_session(resp: AsyncMock) -> MagicMock:
    """Build a mock session whose ``request()`` returns *resp* as a context manager."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=resp)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


class TestQuotaScopeClient:
    @pytest.mark.asyncio
    async def test_get(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"quota_scope": _QUOTA_SCOPE_PAYLOAD})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        qs = QuotaScopeClient(client)

        result = await qs.get("local:volume1", "user:test-user-uuid")

        assert isinstance(result, GetQuotaScopeResponse)
        assert result.quota_scope.quota_scope_id == "user:test-user-uuid"
        assert result.quota_scope.storage_host_name == "local:volume1"
        assert result.quota_scope.hard_limit_bytes == 10737418240

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert "/admin/quota-scopes/local:volume1/user:test-user-uuid" in str(call_args.args[1])
        assert call_args.kwargs["json"] is None

    @pytest.mark.asyncio
    async def test_search(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "quota_scopes": [_QUOTA_SCOPE_PAYLOAD],
                "pagination": {"total": 1, "offset": 0, "limit": 50},
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        qs = QuotaScopeClient(client)

        request = SearchQuotaScopesRequest()
        result = await qs.search(request)

        assert isinstance(result, SearchQuotaScopesResponse)
        assert len(result.quota_scopes) == 1
        assert result.quota_scopes[0].quota_scope_id == "user:test-user-uuid"
        assert result.pagination.total == 1

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/quota-scopes/search" in str(call_args.args[1])

    @pytest.mark.asyncio
    async def test_set_quota(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"quota_scope": _QUOTA_SCOPE_PAYLOAD})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        qs = QuotaScopeClient(client)

        request = SetQuotaRequest(
            storage_host_name="local:volume1",
            quota_scope_id="user:test-user-uuid",
            hard_limit_bytes=10737418240,
        )
        result = await qs.set_quota(request)

        assert isinstance(result, SetQuotaResponse)
        assert result.quota_scope.hard_limit_bytes == 10737418240

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/quota-scopes/set" in str(call_args.args[1])
        assert call_args.kwargs["json"]["storage_host_name"] == "local:volume1"
        assert call_args.kwargs["json"]["quota_scope_id"] == "user:test-user-uuid"
        assert call_args.kwargs["json"]["hard_limit_bytes"] == 10737418240

    @pytest.mark.asyncio
    async def test_unset_quota(self) -> None:
        unset_payload = {
            **_QUOTA_SCOPE_PAYLOAD,
            "hard_limit_bytes": None,
        }
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"quota_scope": unset_payload})

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        qs = QuotaScopeClient(client)

        request = UnsetQuotaRequest(
            storage_host_name="local:volume1",
            quota_scope_id="user:test-user-uuid",
        )
        result = await qs.unset_quota(request)

        assert isinstance(result, UnsetQuotaResponse)
        assert result.quota_scope.hard_limit_bytes is None

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "POST"
        assert "/admin/quota-scopes/unset" in str(call_args.args[1])
        assert call_args.kwargs["json"]["storage_host_name"] == "local:volume1"
        assert call_args.kwargs["json"]["quota_scope_id"] == "user:test-user-uuid"

    @pytest.mark.asyncio
    async def test_search_with_empty_results(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(
            return_value={
                "quota_scopes": [],
                "pagination": {"total": 0, "offset": 0, "limit": 50},
            }
        )

        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        qs = QuotaScopeClient(client)

        request = SearchQuotaScopesRequest()
        result = await qs.search(request)

        assert isinstance(result, SearchQuotaScopesResponse)
        assert len(result.quota_scopes) == 0
        assert result.pagination.total == 0

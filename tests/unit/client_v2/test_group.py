from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.group import GroupClient
from ai.backend.common.dto.manager.registry.request import (
    CreateRegistryQuotaReq,
    DeleteRegistryQuotaReq,
    ReadRegistryQuotaReq,
    UpdateRegistryQuotaReq,
)
from ai.backend.common.dto.manager.registry.response import RegistryQuotaResponse

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


class TestGroupClientRegistryQuota:
    @pytest.mark.asyncio
    async def test_create_registry_quota(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 204
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = GroupClient(client)

        request = CreateRegistryQuotaReq(group_id="g-1", quota=100)
        await domain.create_registry_quota(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "POST"
        assert "/group/registry-quota" in str(call_args[0][1])
        assert call_args.kwargs["json"]["group_id"] == "g-1"
        assert call_args.kwargs["json"]["quota"] == 100

    @pytest.mark.asyncio
    async def test_read_registry_quota(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"result": 50})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = GroupClient(client)

        request = ReadRegistryQuotaReq(group_id="g-2")
        result = await domain.read_registry_quota(request)

        assert isinstance(result, RegistryQuotaResponse)
        assert result.result == 50
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/group/registry-quota" in str(call_args[0][1])
        assert call_args.kwargs["params"] == {"group_id": "g-2"}

    @pytest.mark.asyncio
    async def test_read_registry_quota_passes_group_id_as_query_param(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"result": 10})
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = GroupClient(client)

        request = ReadRegistryQuotaReq(group_id="special-group")
        await domain.read_registry_quota(request)

        call_kwargs = mock_session.request.call_args.kwargs
        assert call_kwargs["params"]["group_id"] == "special-group"
        # Should not send a JSON body for GET
        assert call_kwargs.get("json") is None

    @pytest.mark.asyncio
    async def test_update_registry_quota(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 204
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = GroupClient(client)

        request = UpdateRegistryQuotaReq(group_id="g-3", quota=200)
        await domain.update_registry_quota(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "PATCH"
        assert "/group/registry-quota" in str(call_args[0][1])
        assert call_args.kwargs["json"]["group_id"] == "g-3"
        assert call_args.kwargs["json"]["quota"] == 200

    @pytest.mark.asyncio
    async def test_delete_registry_quota(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 204
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = GroupClient(client)

        request = DeleteRegistryQuotaReq(group_id="g-4")
        await domain.delete_registry_quota(request)

        call_args = mock_session.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "/group/registry-quota" in str(call_args[0][1])
        assert call_args.kwargs["json"]["group_id"] == "g-4"

    @pytest.mark.asyncio
    async def test_create_registry_quota_serializes_body(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 204
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = GroupClient(client)

        request = CreateRegistryQuotaReq(group_id="grp-x", quota=999)
        await domain.create_registry_quota(request)

        body = mock_session.request.call_args.kwargs["json"]
        assert body == {"group_id": "grp-x", "quota": 999}

    @pytest.mark.asyncio
    async def test_delete_registry_quota_sends_only_group_id(self) -> None:
        mock_resp = AsyncMock()
        mock_resp.status = 204
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        domain = GroupClient(client)

        request = DeleteRegistryQuotaReq(group_id="grp-y")
        await domain.delete_registry_quota(request)

        body = mock_session.request.call_args.kwargs["json"]
        assert body == {"group_id": "grp-y"}

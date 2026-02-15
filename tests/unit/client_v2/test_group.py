from __future__ import annotations

from typing import Any
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


def _json_response(data: dict[str, Any], *, status: int = 200) -> AsyncMock:
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=data)
    return resp


def _no_content_response() -> AsyncMock:
    resp = AsyncMock()
    resp.status = 204
    return resp


def _make_group_client(mock_session: MagicMock) -> GroupClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return GroupClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


class TestCreateRegistryQuota:
    @pytest.mark.asyncio
    async def test_sends_post_with_body(self) -> None:
        resp = _no_content_response()
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = CreateRegistryQuotaReq(group_id="grp-001", quota=100)
        await gc.create_registry_quota(request)

        method, url, body = _last_request_call(mock_session)
        assert method == "POST"
        assert "/group/registry-quota" in url
        assert body is not None
        assert body["group_id"] == "grp-001"
        assert body["quota"] == 100


class TestReadRegistryQuota:
    @pytest.mark.asyncio
    async def test_sends_get_with_params(self) -> None:
        resp = _json_response({"result": 100})
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = ReadRegistryQuotaReq(group_id="grp-001")
        result = await gc.read_registry_quota(request)

        assert isinstance(result, RegistryQuotaResponse)
        assert result.result == 100
        call_args = mock_session.request.call_args
        assert call_args[0][0] == "GET"
        assert "/group/registry-quota" in str(call_args[0][1])
        assert call_args.kwargs["params"]["group_id"] == "grp-001"


class TestUpdateRegistryQuota:
    @pytest.mark.asyncio
    async def test_sends_patch_with_body(self) -> None:
        resp = _no_content_response()
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = UpdateRegistryQuotaReq(group_id="grp-001", quota=200)
        await gc.update_registry_quota(request)

        method, url, body = _last_request_call(mock_session)
        assert method == "PATCH"
        assert "/group/registry-quota" in url
        assert body is not None
        assert body["group_id"] == "grp-001"
        assert body["quota"] == 200


class TestDeleteRegistryQuota:
    @pytest.mark.asyncio
    async def test_sends_delete_with_body(self) -> None:
        resp = _no_content_response()
        mock_session = _make_request_session(resp)
        gc = _make_group_client(mock_session)

        request = DeleteRegistryQuotaReq(group_id="grp-001")
        await gc.delete_registry_quota(request)

        method, url, body = _last_request_call(mock_session)
        assert method == "DELETE"
        assert "/group/registry-quota" in url
        assert body is not None
        assert body["group_id"] == "grp-001"

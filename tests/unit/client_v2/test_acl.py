"""Unit tests for ACLClient (SDK v2)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.acl import ACLClient
from ai.backend.common.dto.manager.acl import GetPermissionsResponse

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


def _make_acl_client(mock_session: MagicMock) -> ACLClient:
    client = BackendAIClient(_DEFAULT_CONFIG, MockAuth(), mock_session)
    return ACLClient(client)


def _last_request_call(mock_session: MagicMock) -> tuple[str, str, dict[str, Any] | None]:
    """Return (method, url, json_body) from the last ``session.request()`` call."""
    args, kwargs = mock_session.request.call_args
    return args[0], str(args[1]), kwargs.get("json")


_SAMPLE_PERMISSIONS = [
    "create-vfolder",
    "modify-vfolder",
    "delete-vfolder",
    "mount-in-session",
    "upload-file",
    "download-file",
    "invite-others",
    "set-user-specific-permission",
]


class TestACLClient:
    @pytest.mark.asyncio
    async def test_get_permissions(self) -> None:
        resp = _json_response({
            "vfolder_host_permission_list": _SAMPLE_PERMISSIONS,
        })
        mock_session = _make_request_session(resp)
        ac = _make_acl_client(mock_session)

        result = await ac.get_permissions()

        assert isinstance(result, GetPermissionsResponse)
        assert result.vfolder_host_permission_list == _SAMPLE_PERMISSIONS
        method, url, body = _last_request_call(mock_session)
        assert method == "GET"
        assert url.endswith("/acl")
        assert body is None

    @pytest.mark.asyncio
    async def test_get_permissions_empty_list(self) -> None:
        resp = _json_response({
            "vfolder_host_permission_list": [],
        })
        mock_session = _make_request_session(resp)
        ac = _make_acl_client(mock_session)

        result = await ac.get_permissions()

        assert isinstance(result, GetPermissionsResponse)
        assert result.vfolder_host_permission_list == []

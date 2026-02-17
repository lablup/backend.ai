from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.system import SystemClient
from ai.backend.common.dto.manager.system import SystemVersionResponse

from .conftest import MockAuth

_DEFAULT_CONFIG = ClientConfig(endpoint=URL("https://api.example.com"))


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


def _ok_response(data: dict[str, Any]) -> AsyncMock:
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value=data)
    return mock_resp


class TestSystemClient:
    @pytest.mark.asyncio
    async def test_get_versions(self) -> None:
        mock_resp = _ok_response({
            "version": "v9.20250722",
            "manager": "25.3.0",
        })
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        system = SystemClient(client)

        result = await system.get_versions()

        assert isinstance(result, SystemVersionResponse)
        assert result.version == "v9.20250722"
        assert result.manager == "25.3.0"

        call_args = mock_session.request.call_args
        assert call_args.args[0] == "GET"
        assert str(call_args.args[1]).endswith("/")

    @pytest.mark.asyncio
    async def test_get_versions_different_values(self) -> None:
        mock_resp = _ok_response({
            "version": "v8.20240315",
            "manager": "24.1.0",
        })
        mock_session = _make_request_session(mock_resp)
        client = _make_client(mock_session)
        system = SystemClient(client)

        result = await system.get_versions()

        assert isinstance(result, SystemVersionResponse)
        assert result.version == "v8.20240315"
        assert result.manager == "24.1.0"

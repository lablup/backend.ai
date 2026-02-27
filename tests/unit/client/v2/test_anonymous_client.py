from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from yarl import URL

from ai.backend.client.v2.auth import AuthStrategy
from ai.backend.client.v2.base_client import (
    BackendAIAnonymousClient,
    BackendAIAuthClient,
)
from ai.backend.client.v2.config import ClientConfig


@pytest.fixture
def config() -> ClientConfig:
    return ClientConfig(endpoint=URL("http://localhost:8090"))


class FakeAuth(AuthStrategy):
    def sign(
        self,
        method: str,
        version: str,
        endpoint: URL,
        date: datetime,
        rel_url: str,
        content_type: str,
    ) -> Mapping[str, str]:
        return {"Authorization": "Fake fake-key:fake-sig"}


class TestAnonymousClientBuildHeaders:
    def test_no_authorization_header(self, config: ClientConfig) -> None:
        session = MagicMock(spec=aiohttp.ClientSession)
        client = BackendAIAnonymousClient(config, session)
        headers = client._build_headers("GET", "/auth/authorize", "application/json")
        assert "Authorization" not in headers

    def test_contains_required_headers(self, config: ClientConfig) -> None:
        session = MagicMock(spec=aiohttp.ClientSession)
        client = BackendAIAnonymousClient(config, session)
        headers = client._build_headers("POST", "/auth/signup", "application/json")
        assert "Date" in headers
        assert headers["Content-Type"] == "application/json"
        assert headers["X-BackendAI-Version"] == config.api_version


class TestAuthClientBuildHeaders:
    def test_contains_authorization_header(self, config: ClientConfig) -> None:
        session = MagicMock(spec=aiohttp.ClientSession)
        auth = FakeAuth()
        client = BackendAIAuthClient(config, auth, session)
        headers = client._build_headers("GET", "/api/resource", "application/json")
        assert "Authorization" in headers

    def test_contains_required_headers(self, config: ClientConfig) -> None:
        session = MagicMock(spec=aiohttp.ClientSession)
        auth = FakeAuth()
        client = BackendAIAuthClient(config, auth, session)
        headers = client._build_headers("GET", "/api/resource", "application/json")
        assert "Date" in headers
        assert headers["Content-Type"] == "application/json"
        assert headers["X-BackendAI-Version"] == config.api_version


class TestAnonymousClientRequest:
    @pytest.mark.asyncio
    async def test_request_sends_no_auth_header(self, config: ClientConfig) -> None:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "ok"})

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_response)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock(spec=aiohttp.ClientSession)
        mock_session.request = MagicMock(return_value=mock_ctx)

        client = BackendAIAnonymousClient(config, mock_session)
        result = await client._request("POST", "/auth/authorize", json={"email": "test"})

        mock_session.request.assert_called_once()
        call_kwargs = mock_session.request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"
        assert headers["X-BackendAI-Version"] == config.api_version
        assert result == {"result": "ok"}

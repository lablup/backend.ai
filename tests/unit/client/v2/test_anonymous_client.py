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
from ai.backend.common.dto.manager.auth.request import (
    AuthorizeRequest,
    SignupRequest,
    UpdatePasswordNoAuthRequest,
)
from ai.backend.common.dto.manager.auth.types import AuthTokenType


@pytest.fixture
def config() -> ClientConfig:
    return ClientConfig(endpoint=URL("http://localhost:8090"))


def _mock_session(response_data: dict, *, status: int = 200) -> MagicMock:
    mock_response = AsyncMock()
    mock_response.status = status
    mock_response.json = AsyncMock(return_value=response_data)

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock(spec=aiohttp.ClientSession)
    mock_session.request = MagicMock(return_value=mock_ctx)
    return mock_session


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
        session = _mock_session({"result": "ok"})
        client = BackendAIAnonymousClient(config, session)
        result = await client._request("POST", "/auth/authorize", json={"email": "test"})

        session.request.assert_called_once()
        call_kwargs = session.request.call_args
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert "Authorization" not in headers
        assert headers["Content-Type"] == "application/json"
        assert headers["X-BackendAI-Version"] == config.api_version
        assert result == {"result": "ok"}


class TestAnonymousAuthorize:
    @pytest.mark.asyncio
    async def test_authorize_sends_post(self, config: ClientConfig) -> None:
        response_data = {
            "data": {
                "access_key": "AKTEST",
                "secret_key": "sktest",
                "role": "user",
                "status": "active",
                "response_type": "success",
            },
        }
        session = _mock_session(response_data)
        client = BackendAIAnonymousClient(config, session)
        request = AuthorizeRequest(
            type=AuthTokenType.KEYPAIR,
            domain="default",
            username="user@example.com",
            password="secret",
        )
        result = await client.authorize(request)
        assert result.data.access_key == "AKTEST"

        call_kwargs = session.request.call_args
        assert call_kwargs.args[0] == "POST"
        assert "/auth/authorize" in call_kwargs.args[1]
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert "Authorization" not in headers


class TestAnonymousSignup:
    @pytest.mark.asyncio
    async def test_signup_sends_post(self, config: ClientConfig) -> None:
        response_data = {"access_key": "AKNEW", "secret_key": "sknew"}
        session = _mock_session(response_data)
        client = BackendAIAnonymousClient(config, session)
        request = SignupRequest(
            domain="default",
            email="new@example.com",
            password="newpass123",
        )
        result = await client.signup(request)
        assert result.access_key == "AKNEW"

        call_kwargs = session.request.call_args
        assert call_kwargs.args[0] == "POST"
        assert "/auth/signup" in call_kwargs.args[1]
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert "Authorization" not in headers


class TestAnonymousUpdatePasswordNoAuth:
    @pytest.mark.asyncio
    async def test_update_password_no_auth_sends_post(self, config: ClientConfig) -> None:
        response_data = {"password_changed_at": "2026-01-15T10:00:00+00:00"}
        session = _mock_session(response_data)
        client = BackendAIAnonymousClient(config, session)
        request = UpdatePasswordNoAuthRequest(
            domain="default",
            username="user@example.com",
            current_password="oldpass",
            new_password="newpass456",
        )
        result = await client.update_password_no_auth(request)
        assert result.password_changed_at == "2026-01-15T10:00:00+00:00"

        call_kwargs = session.request.call_args
        assert call_kwargs.args[0] == "POST"
        assert "/auth/update-password-no-auth" in call_kwargs.args[1]
        headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert "Authorization" not in headers

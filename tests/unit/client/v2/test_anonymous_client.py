from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from unittest.mock import MagicMock

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

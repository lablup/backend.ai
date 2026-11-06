from __future__ import annotations

from dataclasses import replace
from unittest.mock import AsyncMock

import click
import pytest
from yarl import URL

from ai.backend.client.cli.v2.helpers import V2ConnectionConfig, create_v2_registry
from ai.backend.client.cli.v2.insecure_http_guard import reject_insecure_endpoint
from ai.backend.client.v2.v2_registry import V2ClientRegistry


@pytest.fixture
def registry_create(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    create = AsyncMock()
    monkeypatch.setattr(V2ClientRegistry, "create", create)
    return create


@pytest.fixture
def v2_config_at_insecure_endpoint() -> V2ConnectionConfig:
    return V2ConnectionConfig(
        endpoint=URL("http://backend.example"),
        endpoint_type="api",
        access_key=None,
        secret_key=None,
        api_version="v9.20250722",
    )


class TestCreateV2Registry:
    async def test_refuses_an_insecure_endpoint(
        self,
        registry_create: AsyncMock,
        v2_config_at_insecure_endpoint: V2ConnectionConfig,
    ) -> None:
        with pytest.raises(click.ClickException):
            await create_v2_registry(v2_config_at_insecure_endpoint)

        registry_create.assert_not_called()

    async def test_creates_the_registry_when_insecure_http_is_allowed(
        self,
        registry_create: AsyncMock,
        v2_config_at_insecure_endpoint: V2ConnectionConfig,
    ) -> None:
        await create_v2_registry(replace(v2_config_at_insecure_endpoint, allow_insecure_http=True))

        registry_create.assert_called_once()


class TestRejectInsecureEndpoint:
    @pytest.mark.parametrize(
        "endpoint",
        [
            "https://backend.example",
            "http://localhost:8090",
            "http://127.0.0.1:8090",
            "http://[::1]:8090",
        ],
    )
    def test_accepts_https_and_loopback(self, endpoint: str) -> None:
        reject_insecure_endpoint(URL(endpoint), allow_insecure_http=False)

    @pytest.mark.parametrize(
        "endpoint",
        [
            "http://backend.example",
            "http://localhost.example",
        ],
    )
    def test_rejects_other_http(self, endpoint: str) -> None:
        with pytest.raises(click.ClickException):
            reject_insecure_endpoint(URL(endpoint), allow_insecure_http=False)

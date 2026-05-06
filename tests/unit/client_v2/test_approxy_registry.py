from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from yarl import URL

from ai.backend.client.v2.approxy_registry import AppProxyClientRegistry
from ai.backend.client.v2.base_appproxy_domain import BaseAppProxyDomainClient
from ai.backend.client.v2.base_client import BackendAIAppProxyClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.deployment_chat import DeploymentChatClient


def _build_appproxy_client(session: MagicMock | None = None) -> BackendAIAppProxyClient:
    """Construct a BackendAIAppProxyClient with the aiohttp session swapped for a mock.

    Bypasses ``_create_aiohttp_session`` so the synchronous constructor does
    not require a running event loop (aiohttp >= 3.13 raises otherwise).
    """
    config = ClientConfig(endpoint=URL("https://api.example.com"))
    with patch(
        "ai.backend.client.v2.base_client._create_aiohttp_session",
        return_value=session if session is not None else MagicMock(),
    ):
        return BackendAIAppProxyClient(config)


class TestAppProxyClientRegistry:
    @pytest.fixture
    def registry(self) -> AppProxyClientRegistry:
        return AppProxyClientRegistry(_build_appproxy_client())

    async def test_create_factory(self) -> None:
        config = ClientConfig(endpoint=URL("https://api.example.com"))
        with patch(
            "ai.backend.client.v2.base_client._create_aiohttp_session",
            return_value=MagicMock(),
        ):
            registry = await AppProxyClientRegistry.create(config)
        assert isinstance(registry._client, BackendAIAppProxyClient)

    def test_domain_clients_return_correct_types(self, registry: AppProxyClientRegistry) -> None:
        assert isinstance(registry.deployment_chat, DeploymentChatClient)

    def test_domain_clients_inherit_base(self, registry: AppProxyClientRegistry) -> None:
        assert isinstance(registry.deployment_chat, BaseAppProxyDomainClient)

    def test_cached_property_returns_same_instance(self, registry: AppProxyClientRegistry) -> None:
        first = registry.deployment_chat
        second = registry.deployment_chat
        assert first is second

    async def test_close_delegates_to_client(self) -> None:
        mock_session = AsyncMock()
        mock_session.closed = False
        client = _build_appproxy_client(mock_session)
        registry = AppProxyClientRegistry(client)
        await registry.close()
        mock_session.close.assert_awaited_once()

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from yarl import URL

from ai.backend.client.v2.base_client import BackendAIClient
from ai.backend.client.v2.base_domain import BaseDomainClient
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.domains.auth import AuthClient
from ai.backend.client.v2.domains.config import ConfigClient
from ai.backend.client.v2.domains.container_registry import ContainerRegistryClient
from ai.backend.client.v2.domains.fair_share import FairShareClient
from ai.backend.client.v2.domains.group import GroupClient
from ai.backend.client.v2.domains.infra import InfraClient
from ai.backend.client.v2.domains.model_serving import ModelServingClient
from ai.backend.client.v2.domains.operations import OperationsClient
from ai.backend.client.v2.domains.session import SessionClient
from ai.backend.client.v2.domains.storage import StorageClient
from ai.backend.client.v2.domains.streaming import StreamingClient
from ai.backend.client.v2.domains.template import TemplateClient
from ai.backend.client.v2.domains.vfolder import VFolderClient
from ai.backend.client.v2.registry import BackendAIClientRegistry

from .conftest import MockAuth


class TestBackendAIClientRegistry:
    @pytest.fixture
    def registry(self) -> BackendAIClientRegistry:
        config = ClientConfig(endpoint=URL("https://api.example.com"))
        mock_session = MagicMock(spec_set=["request", "close"])
        client = BackendAIClient(config, MockAuth(), mock_session)
        return BackendAIClientRegistry(client)

    @pytest.mark.asyncio
    async def test_create_factory(self) -> None:
        config = ClientConfig(endpoint=URL("https://api.example.com"))
        with patch("ai.backend.client.v2.base_client.aiohttp.ClientSession") as mock_cls:
            mock_cls.return_value = MagicMock()
            registry = await BackendAIClientRegistry.create(config, MockAuth())
            assert isinstance(registry._client, BackendAIClient)

    def test_domain_clients_return_correct_types(self, registry: BackendAIClientRegistry) -> None:
        assert isinstance(registry.session, SessionClient)
        assert isinstance(registry.vfolder, VFolderClient)
        assert isinstance(registry.model_serving, ModelServingClient)
        assert isinstance(registry.auth, AuthClient)
        assert isinstance(registry.streaming, StreamingClient)
        assert isinstance(registry.config, ConfigClient)
        assert isinstance(registry.infra, InfraClient)
        assert isinstance(registry.template, TemplateClient)
        assert isinstance(registry.operations, OperationsClient)
        assert isinstance(registry.container_registry, ContainerRegistryClient)
        assert isinstance(registry.group, GroupClient)
        assert isinstance(registry.storage, StorageClient)
        assert isinstance(registry.fair_share, FairShareClient)

    def test_domain_clients_inherit_base(self, registry: BackendAIClientRegistry) -> None:
        assert isinstance(registry.session, BaseDomainClient)
        assert isinstance(registry.vfolder, BaseDomainClient)

    def test_cached_property_returns_same_instance(self, registry: BackendAIClientRegistry) -> None:
        first = registry.vfolder
        second = registry.vfolder
        assert first is second

    def test_different_domains_are_different_instances(
        self, registry: BackendAIClientRegistry
    ) -> None:
        assert id(registry.session) != id(registry.vfolder)

    @pytest.mark.asyncio
    async def test_close_delegates_to_client(self) -> None:
        mock_session = AsyncMock()
        config = ClientConfig(endpoint=URL("https://api.example.com"))
        client = BackendAIClient(config, MockAuth(), mock_session)
        registry = BackendAIClientRegistry(client)
        await registry.close()
        mock_session.close.assert_awaited_once()

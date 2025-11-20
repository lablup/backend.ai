from typing import Any, AsyncGenerator, Mapping
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import (
    AgentId,
    ValkeyTarget,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.repository import AgentRepository


class TestAgentRepository:
    @pytest.fixture
    async def valkey_image_client(
        self,
        redis_container: tuple[str, tuple[str, int]],
    ) -> AsyncGenerator[ValkeyImageClient, None]:
        """Create ValkeyImageClient with real Redis container (db_id=1)"""
        _, redis_addr = redis_container

        valkey_target = ValkeyTarget(
            addr=f"{redis_addr[0]}:{redis_addr[1]}",
        )

        client = await ValkeyImageClient.create(
            valkey_target=valkey_target,
            db_id=1,
            human_readable_name="test-valkey-image",
        )

        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    async def valkey_live_client(
        self,
        redis_container: tuple[str, tuple[str, int]],
    ) -> AsyncGenerator[ValkeyLiveClient, None]:
        """Create ValkeyLiveClient with real Redis container (db_id=2)"""
        _, redis_addr = redis_container

        valkey_target = ValkeyTarget(
            addr=f"{redis_addr[0]}:{redis_addr[1]}",
        )

        client = await ValkeyLiveClient.create(
            valkey_target=valkey_target,
            db_id=2,
            human_readable_name="test-valkey-live",
        )

        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    async def valkey_stat_client(
        self,
        redis_container: tuple[str, tuple[str, int]],
    ) -> AsyncGenerator[ValkeyStatClient, None]:
        """Create ValkeyStatClient with real Redis container (db_id=3)"""
        _, redis_addr = redis_container

        valkey_target = ValkeyTarget(
            addr=f"{redis_addr[0]}:{redis_addr[1]}",
        )

        client = await ValkeyStatClient.create(
            valkey_target=valkey_target,
            db_id=3,
            human_readable_name="test-valkey-stat",
        )

        try:
            yield client
        finally:
            await client.close()

    @pytest.fixture
    def mock_config_provider(self) -> MagicMock:
        """Mock config provider for legacy etcd operations"""
        mock = MagicMock(spec=ManagerConfigProvider)
        mock.legacy_etcd_config_loader = AsyncMock()
        mock.legacy_etcd_config_loader.update_resource_slots = AsyncMock()
        return mock

    @pytest.fixture
    def mock_database_engine(self) -> MagicMock:
        """Mock database engine - not needed for cache-only tests"""
        return MagicMock(spec=ExtendedAsyncSAEngine)

    @pytest.fixture
    async def agent_repository(
        self,
        mock_database_engine: MagicMock,
        valkey_image_client: ValkeyImageClient,
        valkey_live_client: ValkeyLiveClient,
        valkey_stat_client: ValkeyStatClient,
        mock_config_provider: MagicMock,
    ) -> AsyncGenerator[AgentRepository, None]:
        """Create AgentRepository with real Redis clients and mock database"""
        repo = AgentRepository(
            db=mock_database_engine,
            valkey_image=valkey_image_client,
            valkey_live=valkey_live_client,
            valkey_stat=valkey_stat_client,
            config_provider=mock_config_provider,
        )
        yield repo

    @pytest.mark.asyncio
    async def test_update_gpu_alloc_map(
        self,
        agent_repository: AgentRepository,
        valkey_stat_client: ValkeyStatClient,
    ) -> None:
        """Test GPU allocation map update is stored in cache"""
        # Given
        agent_id = AgentId("agent-001")
        alloc_map: Mapping[str, Any] = {
            "cuda:0": {"session_id": "sess-001"},
            "cuda:1": {"session_id": "sess-002"},
        }

        # When
        await agent_repository.update_gpu_alloc_map(agent_id, alloc_map)

        # Then - verify data was written to Redis
        stored_map = await valkey_stat_client.get_gpu_allocation_map(str(agent_id))
        assert stored_map == alloc_map

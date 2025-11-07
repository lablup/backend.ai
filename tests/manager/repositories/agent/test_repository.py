from datetime import datetime
from typing import Any, AsyncGenerator, Mapping
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dateutil.tz import tzutc

from ai.backend.common.auth import PublicKey
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.types import (
    AgentId,
    ResourceSlot,
    SlotName,
    SlotTypes,
    ValkeyTarget,
)
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import AgentData, AgentDataExtended, AgentStatus
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.options import (
    AgentQueryConditions,
    AgentQueryOrders,
    ListAgentQueryOptions,
)
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

    @pytest.mark.asyncio
    async def test_list_data_delegates_to_db_source(
        self,
        agent_repository: AgentRepository,
    ) -> None:
        """Test list_data properly delegates to db_source"""
        # Given
        options = ListAgentQueryOptions(
            conditions=[AgentQueryConditions.by_scaling_group("default")],
            orders=[AgentQueryOrders.id(ascending=True)],
        )

        expected_agents = [
            AgentData(
                id=AgentId("agent-001"),
                status=AgentStatus.ALIVE,
                status_changed=datetime.now(tzutc()),
                region="us-west-1",
                scaling_group="default",
                schedulable=True,
                available_slots=ResourceSlot({SlotName("cpu"): 8.0}),
                cached_occupied_slots=ResourceSlot({}),
                actual_occupied_slots=ResourceSlot({}),
                addr="tcp://192.168.1.100:6001",
                public_host="192.168.1.100",
                first_contact=datetime.now(tzutc()),
                lost_at=None,
                version="24.12.0",
                architecture="x86_64",
                compute_plugins=[],
                public_key=PublicKey(b"test-public-key"),
                auto_terminate_abusing_kernel=False,
            ),
            AgentData(
                id=AgentId("agent-002"),
                status=AgentStatus.ALIVE,
                status_changed=datetime.now(tzutc()),
                region="us-west-1",
                scaling_group="default",
                schedulable=True,
                available_slots=ResourceSlot({SlotName("cpu"): 16.0}),
                cached_occupied_slots=ResourceSlot({}),
                actual_occupied_slots=ResourceSlot({}),
                addr="tcp://192.168.1.101:6001",
                public_host="192.168.1.101",
                first_contact=datetime.now(tzutc()),
                lost_at=None,
                version="24.12.0",
                architecture="x86_64",
                compute_plugins=[],
                public_key=PublicKey(b"test-public-key-2"),
                auto_terminate_abusing_kernel=False,
            ),
        ]

        # When
        with patch.object(
            agent_repository._db_source,
            "fetch_agent_data_list",
            new=AsyncMock(return_value=expected_agents),
        ) as mock_fetch:
            result = await agent_repository.list_data(options)

            # Then
            assert len(result) == 2
            assert result[0].id == AgentId("agent-001")
            assert result[1].id == AgentId("agent-002")
            assert all(agent.scaling_group == "default" for agent in result)
            mock_fetch.assert_called_once_with(options)

    @pytest.mark.asyncio
    async def test_list_data_with_empty_result(
        self,
        agent_repository: AgentRepository,
    ) -> None:
        """Test list_data returns empty list when no agents match"""
        # Given
        options = ListAgentQueryOptions(
            conditions=[AgentQueryConditions.by_scaling_group("non-existent")],
            orders=[],
        )

        # When
        with patch.object(
            agent_repository._db_source,
            "fetch_agent_data_list",
            new=AsyncMock(return_value=[]),
        ) as mock_fetch:
            result = await agent_repository.list_data(options)

            # Then
            assert len(result) == 0
            mock_fetch.assert_called_once_with(options)

    @pytest.mark.asyncio
    async def test_list_extended_data_delegates_to_db_source(
        self,
        agent_repository: AgentRepository,
        mock_config_provider: MagicMock,
    ) -> None:
        """Test list_extended_data properly delegates to db_source with requirements"""
        # Given
        options = ListAgentQueryOptions(
            conditions=[AgentQueryConditions.by_statuses([AgentStatus.ALIVE])],
            orders=[AgentQueryOrders.id(ascending=False)],
        )

        known_slot_types = {
            SlotName("cpu"): SlotTypes.COUNT,
            SlotName("mem"): SlotTypes.BYTES,
            SlotName("cuda.shares"): SlotTypes.COUNT,
        }

        # Mock config provider to return known slot types
        mock_config_provider.legacy_etcd_config_loader.get_resource_slots = AsyncMock(
            return_value=known_slot_types
        )

        expected_agents = [
            AgentDataExtended(
                id=AgentId("agent-002"),
                status=AgentStatus.ALIVE,
                status_changed=datetime.now(tzutc()),
                region="us-west-1",
                scaling_group="default",
                schedulable=True,
                available_slots=ResourceSlot({SlotName("cpu"): 16.0}),
                cached_occupied_slots=ResourceSlot({}),
                actual_occupied_slots=ResourceSlot({}),
                addr="tcp://192.168.1.101:6001",
                public_host="192.168.1.101",
                first_contact=datetime.now(tzutc()),
                lost_at=None,
                version="24.12.0",
                architecture="x86_64",
                compute_plugins=[],
                public_key=PublicKey(b"test-public-key-2"),
                auto_terminate_abusing_kernel=False,
                known_slot_types=known_slot_types,
                kernels=[],
            ),
            AgentDataExtended(
                id=AgentId("agent-001"),
                status=AgentStatus.ALIVE,
                status_changed=datetime.now(tzutc()),
                region="us-west-1",
                scaling_group="default",
                schedulable=True,
                available_slots=ResourceSlot({SlotName("cpu"): 8.0}),
                cached_occupied_slots=ResourceSlot({}),
                actual_occupied_slots=ResourceSlot({}),
                addr="tcp://192.168.1.100:6001",
                public_host="192.168.1.100",
                first_contact=datetime.now(tzutc()),
                lost_at=None,
                version="24.12.0",
                architecture="x86_64",
                compute_plugins=[],
                public_key=PublicKey(b"test-public-key"),
                auto_terminate_abusing_kernel=False,
                known_slot_types=known_slot_types,
                kernels=[],
            ),
        ]

        # When
        with patch.object(
            agent_repository._db_source,
            "fetch_agent_extended_data_list",
            new=AsyncMock(return_value=expected_agents),
        ) as mock_fetch:
            result = await agent_repository.list_extended_data(options)

            # Then
            assert len(result) == 2
            assert result[0].id == AgentId("agent-002")
            assert result[1].id == AgentId("agent-001")
            assert all(agent.status == AgentStatus.ALIVE for agent in result)
            assert all(agent.known_slot_types == known_slot_types for agent in result)

            # Verify config provider was called to get slot types
            mock_config_provider.legacy_etcd_config_loader.get_resource_slots.assert_called_once()

            # Verify db_source was called with correct arguments
            mock_fetch.assert_called_once()
            call_args = mock_fetch.call_args
            assert call_args[0][0] == options
            assert call_args[0][1].known_slot_types == known_slot_types

    @pytest.mark.asyncio
    async def test_list_extended_data_with_multiple_conditions(
        self,
        agent_repository: AgentRepository,
        mock_config_provider: MagicMock,
    ) -> None:
        """Test list_extended_data with multiple query conditions"""
        # Given
        options = ListAgentQueryOptions(
            conditions=[
                AgentQueryConditions.by_scaling_group("gpu-group"),
                AgentQueryConditions.by_statuses([AgentStatus.ALIVE, AgentStatus.RESTARTING]),
            ],
            orders=[AgentQueryOrders.scaling_group(ascending=True)],
        )

        known_slot_types = {
            SlotName("cpu"): SlotTypes.COUNT,
            SlotName("mem"): SlotTypes.BYTES,
        }

        mock_config_provider.legacy_etcd_config_loader.get_resource_slots = AsyncMock(
            return_value=known_slot_types
        )

        expected_agent = AgentDataExtended(
            id=AgentId("agent-gpu-001"),
            status=AgentStatus.ALIVE,
            status_changed=datetime.now(tzutc()),
            region="us-east-1",
            scaling_group="gpu-group",
            schedulable=True,
            available_slots=ResourceSlot({SlotName("cpu"): 32.0}),
            cached_occupied_slots=ResourceSlot({}),
            actual_occupied_slots=ResourceSlot({}),
            addr="tcp://192.168.2.100:6001",
            public_host="192.168.2.100",
            first_contact=datetime.now(tzutc()),
            lost_at=None,
            version="24.12.0",
            architecture="x86_64",
            compute_plugins=[],
            public_key=PublicKey(b"test-public-key-gpu"),
            auto_terminate_abusing_kernel=False,
            known_slot_types=known_slot_types,
            kernels=[],
        )

        # When
        with patch.object(
            agent_repository._db_source,
            "fetch_agent_extended_data_list",
            new=AsyncMock(return_value=[expected_agent]),
        ) as mock_fetch:
            result = await agent_repository.list_extended_data(options)

            # Then
            assert len(result) == 1
            assert result[0].id == AgentId("agent-gpu-001")
            assert result[0].scaling_group == "gpu-group"
            mock_fetch.assert_called_once()

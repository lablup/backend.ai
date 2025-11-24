from collections.abc import AsyncGenerator, AsyncIterator, Generator, Mapping
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import sqlalchemy as sa
from dateutil.tz import tzutc

from ai.backend.common.auth import PublicKey
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.exception import AgentNotFound
from ai.backend.common.types import (
    AgentId,
    DeviceName,
    ResourceSlot,
    SlotName,
    SlotTypes,
    ValkeyTarget,
)
from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import (
    AgentDataExtended,
    AgentHeartbeatUpsert,
    AgentStatus,
)
from ai.backend.manager.errors.resource import ScalingGroupNotFound
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.db_source.db_source import AgentDBSource
from ai.backend.manager.repositories.agent.options import (
    AgentConditions,
    AgentOrders,
)
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.base import OffsetPagination, Querier


@dataclass
class _SampleAgent:
    agent_id: AgentId
    heartbeat_upsert: AgentHeartbeatUpsert


class TestAgentRepository:
    @actxmgr
    async def _create_agents(
        self,
        db_source: AgentDBSource,
        scaling_group: str,
        count: int = 1,
        **overrides: Any,
    ) -> AsyncIterator[list[_SampleAgent]]:
        """Create multiple test agents and yield them, cleaning up afterwards

        Args:
            db_source: Database source for agent operations
            scaling_group: Scaling group name for the agents
            count: Number of agents to create
            **overrides: Override default agent info attributes
        """
        agents: list[_SampleAgent] = []
        agent_ids: list[AgentId] = []

        try:
            for i in range(count):
                agent_id = AgentId(f"agent-{uuid4().hex[:8]}")
                agent_ids.append(agent_id)

                agent_info = AgentInfo(
                    ip=overrides.get("ip", f"192.168.1.{100 + i}"),
                    version=overrides.get("version", "24.12.0"),
                    scaling_group=scaling_group,
                    available_resource_slots=overrides.get(
                        "available_resource_slots",
                        ResourceSlot({
                            SlotName("cpu"): "8",
                            SlotName("mem"): "32768",
                            SlotName("cuda.shares"): "4",
                        }),
                    ),
                    slot_key_and_units=overrides.get(
                        "slot_key_and_units",
                        {
                            SlotName("cpu"): SlotTypes.COUNT,
                            SlotName("mem"): SlotTypes.BYTES,
                            SlotName("cuda.shares"): SlotTypes.COUNT,
                        },
                    ),
                    compute_plugins=overrides.get(
                        "compute_plugins",
                        {DeviceName("cpu"): {"brand": "Intel", "model": "Core i7"}},
                    ),
                    addr=overrides.get("addr", f"tcp://192.168.1.{100 + i}:6001"),
                    public_key=overrides.get("public_key", PublicKey(f"key-{100 + i}".encode())),
                    public_host=overrides.get("public_host", f"192.168.1.{100 + i}"),
                    images=overrides.get("images", b"\x82\xc4\x00\x00"),
                    region=overrides.get("region", "us-west-1"),
                    architecture=overrides.get("architecture", "x86_64"),
                    auto_terminate_abusing_kernel=overrides.get(
                        "auto_terminate_abusing_kernel", False
                    ),
                )

                heartbeat_upsert = AgentHeartbeatUpsert.from_agent_info(
                    agent_id=agent_id,
                    agent_info=agent_info,
                    heartbeat_received=datetime.now(tzutc()),
                )

                await db_source.upsert_agent_with_state(heartbeat_upsert)
                agents.append(_SampleAgent(agent_id=agent_id, heartbeat_upsert=heartbeat_upsert))

            yield agents

        finally:
            # Cleanup
            async with db_source._db.begin_session() as db_session:
                for agent_id in agent_ids:
                    await db_session.execute(sa.delete(AgentRow).where(AgentRow.id == agent_id))

    @pytest.fixture
    async def scaling_group(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[str, None]:
        """Create a test scaling group"""
        group_name = f"test-sgroup-{uuid4().hex[:8]}"

        async with database_engine.begin_session() as db_session:
            scaling_group = ScalingGroupRow(
                name=group_name,
                driver="test",
                scheduler="test",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_session.add(scaling_group)
            await db_session.flush()

        try:
            yield group_name
        finally:
            async with database_engine.begin_session() as db_session:
                await db_session.execute(
                    sa.delete(ScalingGroupRow).where(ScalingGroupRow.name == group_name)
                )

    @pytest.fixture
    async def valkey_image_client(
        self, redis_container: tuple[str, tuple[str, int]]
    ) -> AsyncGenerator[ValkeyImageClient, None]:
        """Create ValkeyImageClient with real Redis container"""
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
        self, redis_container: tuple[str, tuple[str, int]]
    ) -> AsyncGenerator[ValkeyLiveClient, None]:
        """Create ValkeyLiveClient with real Redis container"""
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
        self, redis_container: tuple[str, tuple[str, int]]
    ) -> AsyncGenerator[ValkeyStatClient, None]:
        """Create ValkeyStatClient with real Redis container"""
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
    async def db_source(
        self, database_engine: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[AgentDBSource, None]:
        """Create AgentDBSource with real database engine"""
        yield AgentDBSource(db=database_engine)

    @pytest.fixture
    async def mock_config_provider(self) -> AsyncGenerator[ManagerConfigProvider, None]:
        mock_provider = MagicMock(spec=ManagerConfigProvider)
        mock_legacy_loader = MagicMock(spec=LegacyEtcdLoader)
        mock_provider.legacy_etcd_config_loader = mock_legacy_loader
        yield mock_provider

    @pytest.fixture
    async def agent_repository(
        self,
        database_engine: ExtendedAsyncSAEngine,
        valkey_image_client: ValkeyImageClient,
        valkey_live_client: ValkeyLiveClient,
        valkey_stat_client: ValkeyStatClient,
        mock_config_provider: ManagerConfigProvider,
    ) -> AsyncGenerator[AgentRepository, None]:
        """Create AgentRepository with real database and Redis clients"""
        yield AgentRepository(
            db=database_engine,
            valkey_image=valkey_image_client,
            valkey_live=valkey_live_client,
            valkey_stat=valkey_stat_client,
            config_provider=mock_config_provider,
        )

    @pytest.fixture
    def mock_get_resource_slots(
        self, agent_repository: AgentRepository
    ) -> Generator[AsyncMock, None, None]:
        mock = AsyncMock(
            return_value={
                SlotName("cpu"): SlotTypes.COUNT,
                SlotName("mem"): SlotTypes.BYTES,
                SlotName("cuda.shares"): SlotTypes.COUNT,
            }
        )
        with patch.object(
            agent_repository._config_provider.legacy_etcd_config_loader,
            "get_resource_slots",
            mock,
        ):
            yield mock

    @pytest.mark.asyncio
    async def test_db_source_get_by_id_existing_agent(
        self,
        db_source: AgentDBSource,
        scaling_group: str,
    ) -> None:
        """Test getting an existing agent by ID"""
        # Given
        async with self._create_agents(db_source, scaling_group, count=1) as agents:
            agent_id = agents[0].agent_id

            # When
            result = await db_source.get_by_id(agent_id)

            # Then
            assert result.id == agent_id
            assert result.status == AgentStatus.ALIVE

    @pytest.mark.asyncio
    async def test_db_source_get_by_id_nonexistent_agent(
        self,
        db_source: AgentDBSource,
    ) -> None:
        """Test getting a non-existent agent raises AgentNotFound"""
        agent_id = AgentId("nonexistent-agent")

        # When & Then
        with pytest.raises(AgentNotFound):
            await db_source.get_by_id(agent_id)

    @pytest.mark.asyncio
    async def test_db_source_upsert_new_agent(
        self,
        db_source: AgentDBSource,
        scaling_group: str,
    ) -> None:
        """Test upserting a new agent creates it successfully"""
        # When - create new agent
        async with self._create_agents(
            db_source,
            scaling_group,
            count=1,
            ip="192.168.1.200",
            public_key=PublicKey(b"new-agent-key"),
        ) as agents:
            agent_id = agents[0].agent_id

            # Then - verify agent was created successfully
            agent_data = await db_source.get_by_id(agent_id)
            assert agent_data.id == agent_id
            assert agent_data.status == AgentStatus.ALIVE

    @pytest.mark.asyncio
    async def test_db_source_upsert_existing_agent_alive(
        self,
        db_source: AgentDBSource,
        scaling_group: str,
        database_engine: ExtendedAsyncSAEngine,
    ) -> None:
        """Test upserting an existing alive agent"""
        # Given - create an existing agent
        async with self._create_agents(db_source, scaling_group, count=1) as agents:
            agent_id = agents[0].agent_id
            original_upsert = agents[0].heartbeat_upsert
            different_version = "changed-version"
            different_region = "changed-region"

            # Create updated heartbeat with modified version
            updated_upsert = AgentHeartbeatUpsert.from_agent_info(
                agent_id=agent_id,
                agent_info=AgentInfo(
                    ip=original_upsert.network_info.addr.split("//")[1].split(":")[0],
                    version=different_version,  # Different version
                    scaling_group=original_upsert.metadata.scaling_group,
                    available_resource_slots=original_upsert.resource_info.available_slots,
                    slot_key_and_units=dict(original_upsert.resource_info.slot_key_and_units),
                    compute_plugins={
                        k: dict(v) for k, v in original_upsert.resource_info.compute_plugins.items()
                    },
                    addr=original_upsert.network_info.addr,
                    public_key=original_upsert.network_info.public_key,
                    public_host=original_upsert.network_info.public_host,
                    images=b"\x82\xc4\x00\x00",
                    region=different_region,  # Different region
                    architecture=original_upsert.metadata.architecture,
                    auto_terminate_abusing_kernel=original_upsert.metadata.auto_terminate_abusing_kernel,
                ),
                heartbeat_received=datetime.now(tzutc()),
            )

            # When
            result = await db_source.upsert_agent_with_state(updated_upsert)

            # Then
            assert result.was_revived is False
            assert result.need_resource_slot_update is True
            async with database_engine.begin_readonly_session() as db_session:
                agent_row: AgentRow = await db_session.scalar(
                    sa.select(AgentRow).where(AgentRow.id == agent_id)
                )
                assert agent_row.version == different_version
                assert agent_row.region == different_region

    @pytest.mark.asyncio
    async def test_db_source_upsert_scaling_group_not_found(
        self,
        db_source: AgentDBSource,
    ) -> None:
        """Test upserting with non-existent scaling group raises error"""
        agent_id = AgentId(f"agent-fail-{uuid4().hex[:8]}")

        # Create agent info with non-existent scaling group
        agent_info = AgentInfo(
            ip="192.168.1.100",
            version="24.12.0",
            scaling_group="nonexistent-group",
            available_resource_slots=ResourceSlot({
                SlotName("cpu"): "8",
                SlotName("mem"): "32768",
                SlotName("cuda.shares"): "4",
            }),
            slot_key_and_units={
                SlotName("cpu"): SlotTypes.COUNT,
                SlotName("mem"): SlotTypes.BYTES,
                SlotName("cuda.shares"): SlotTypes.COUNT,
            },
            compute_plugins={DeviceName("cpu"): {"brand": "Intel", "model": "Core i7"}},
            addr="tcp://192.168.1.100:6001",
            public_key=PublicKey(b"test-key"),
            public_host="192.168.1.100",
            images=b"\x82\xc4\x00\x00",
            region="us-west-1",
            architecture="x86_64",
            auto_terminate_abusing_kernel=False,
        )

        heartbeat_upsert = AgentHeartbeatUpsert.from_agent_info(
            agent_id=agent_id,
            agent_info=agent_info,
            heartbeat_received=datetime.now(tzutc()),
        )

        # When & Then
        with pytest.raises(ScalingGroupNotFound):
            await db_source.upsert_agent_with_state(heartbeat_upsert)

    @pytest.mark.asyncio
    async def test_db_source_list_agents_no_filter(
        self,
        db_source: AgentDBSource,
        scaling_group: str,
    ) -> None:
        """Test listing all agents without filter"""
        # Given - create a test agent
        async with self._create_agents(db_source, scaling_group, count=1) as agents:
            agent_id = agents[0].agent_id

            # When
            result = await db_source.fetch_agent_data_list()

            # Then
            assert len(result) >= 1
            agent_ids = [agent.id for agent in result]
            assert agent_id in agent_ids

    @pytest.mark.asyncio
    async def test_db_source_list_agents_with_querier(
        self,
        db_source: AgentDBSource,
        scaling_group: str,
    ) -> None:
        """Test listing agents with querier conditions"""
        # Given - create a test agent
        async with self._create_agents(db_source, scaling_group, count=1) as agents:
            agent_id = agents[0].agent_id

            # When
            querier = Querier(
                conditions=[AgentConditions.by_scaling_group(scaling_group)],
                orders=[AgentOrders.id(ascending=True)],
            )
            result = await db_source.fetch_agent_data_list(querier)

            # Then
            assert len(result) >= 1
            assert all(agent.scaling_group == scaling_group for agent in result)
            agent_ids = [agent.id for agent in result]
            assert agent_id in agent_ids

    @pytest.mark.asyncio
    @pytest.mark.parametrize("ascending", [True, False])
    async def test_db_source_list_agents_order(
        self,
        db_source: AgentDBSource,
        scaling_group: str,
        ascending: bool,
    ) -> None:
        """Test listing agents with different sort orders"""
        # Given - create multiple agents
        async with self._create_agents(db_source, scaling_group, count=3) as agents:
            agent_ids = [agent.agent_id for agent in agents]

            # When
            querier = Querier(
                conditions=[AgentConditions.by_scaling_group(scaling_group)],
                orders=[AgentOrders.id(ascending=ascending)],
            )
            result = await db_source.fetch_agent_data_list(querier)

            # Then
            result_ids = [agent.id for agent in result if agent.id in agent_ids]
            sorted_ids = sorted(agent_ids, reverse=not ascending)
            assert result_ids == sorted_ids

    @pytest.mark.asyncio
    async def test_db_source_list_agents_with_pagination(
        self,
        db_source: AgentDBSource,
        scaling_group: str,
    ) -> None:
        """Test listing agents with pagination"""
        # Given - create multiple agents
        async with self._create_agents(db_source, scaling_group, count=5) as agents:
            agent_ids = [agent.agent_id for agent in agents]
            # Sort agent_ids for expected order
            sorted_agent_ids = sorted(agent_ids)

            # When - get first page
            querier = Querier(
                conditions=[AgentConditions.by_scaling_group(scaling_group)],
                orders=[AgentOrders.id(ascending=True)],
                pagination=OffsetPagination(limit=2, offset=0),
            )
            first_page = await db_source.fetch_agent_data_list(querier)

            # Then - verify first page has correct data
            assert len(first_page) == 2
            first_page_ids = [agent.id for agent in first_page]
            assert first_page_ids == sorted_agent_ids[0:2]
            assert all(agent.scaling_group == scaling_group for agent in first_page)

            # When - get second page
            second_querier = Querier(
                conditions=[AgentConditions.by_scaling_group(scaling_group)],
                orders=[AgentOrders.id(ascending=True)],
                pagination=OffsetPagination(limit=2, offset=2),
            )
            second_page = await db_source.fetch_agent_data_list(second_querier)

            # Then - verify second page has correct data
            assert len(second_page) == 2
            second_page_ids = [agent.id for agent in second_page]
            assert second_page_ids == sorted_agent_ids[2:4]
            assert all(agent.scaling_group == scaling_group for agent in second_page)

            # When - get third page (last page with 1 item)
            third_querier = Querier(
                conditions=[AgentConditions.by_scaling_group(scaling_group)],
                orders=[AgentOrders.id(ascending=True)],
                pagination=OffsetPagination(limit=2, offset=4),
            )
            third_page = await db_source.fetch_agent_data_list(third_querier)

            # Then - verify third page has correct data
            assert len(third_page) == 1
            third_page_ids = [agent.id for agent in third_page]
            assert third_page_ids == sorted_agent_ids[4:5]
            assert all(agent.scaling_group == scaling_group for agent in third_page)

            # Verify no overlap between pages
            all_page_ids = first_page_ids + second_page_ids + third_page_ids
            assert len(all_page_ids) == len(set(all_page_ids))  # No duplicates
            assert set(all_page_ids) == set(sorted_agent_ids)  # All agents retrieved

    @pytest.mark.asyncio
    async def test_repository_update_gpu_alloc_map(
        self,
        agent_repository: AgentRepository,
        db_source: AgentDBSource,
        valkey_stat_client: ValkeyStatClient,
        scaling_group: str,
    ) -> None:
        """Test GPU allocation map update via repository"""
        # Given - create a test agent
        async with self._create_agents(db_source, scaling_group, count=1) as agents:
            agent_id = agents[0].agent_id
            alloc_map: Mapping[str, Any] = {
                "cuda:0": {"session_id": "sess-001"},
                "cuda:1": {"session_id": "sess-002"},
            }

            # When
            await agent_repository.update_gpu_alloc_map(agent_id, alloc_map)

            # Then
            stored_map = await valkey_stat_client.get_gpu_allocation_map(str(agent_id))
            assert stored_map == alloc_map

    @pytest.mark.asyncio
    async def test_repository_list_data(
        self,
        agent_repository: AgentRepository,
        db_source: AgentDBSource,
        scaling_group: str,
    ) -> None:
        """Test repository list_data returns agents correctly"""
        # Given - create test agents
        async with self._create_agents(db_source, scaling_group, count=2) as agents:
            agent_ids = [agent.agent_id for agent in agents]

            # When
            querier = Querier(
                conditions=[AgentConditions.by_scaling_group(scaling_group)],
                orders=[AgentOrders.id(ascending=True)],
            )
            result = await agent_repository.list_data(querier)

            # Then
            assert len(result) >= 2
            assert all(agent.scaling_group == scaling_group for agent in result)
            result_ids = [agent.id for agent in result]
            for agent_id in agent_ids:
                assert agent_id in result_ids

    @pytest.mark.parametrize(
        "status_filter, expected_min_count",
        [
            ([AgentStatus.ALIVE], 1),
            ([AgentStatus.LOST], 0),
            ([AgentStatus.TERMINATED], 0),
        ],
    )
    @pytest.mark.asyncio
    async def test_repository_list_data_with_status_filter(
        self,
        agent_repository: AgentRepository,
        db_source: AgentDBSource,
        scaling_group: str,
        status_filter: list[AgentStatus],
        expected_min_count: int,
    ) -> None:
        """Test repository list_data with status filter"""
        # Given - create a test agent
        async with self._create_agents(db_source, scaling_group, count=1):
            # When
            querier = Querier(
                conditions=[AgentConditions.by_statuses(status_filter)],
                orders=[],
            )
            result = await agent_repository.list_data(querier)

            # Then
            assert len(result) >= expected_min_count
            assert all(agent.status in status_filter for agent in result)

    @pytest.mark.asyncio
    async def test_repository_list_data_empty_result(
        self,
        agent_repository: AgentRepository,
    ) -> None:
        """Test repository list_data returns empty list for no matches"""
        # When
        querier = Querier(
            conditions=[AgentConditions.by_scaling_group("nonexistent-group")],
            orders=[],
        )
        result = await agent_repository.list_data(querier)

        # Then
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_repository_list_extended_data(
        self,
        agent_repository: AgentRepository,
        db_source: AgentDBSource,
        scaling_group: str,
        mock_get_resource_slots: AsyncMock,
    ) -> None:
        """Test repository list_extended_data returns agents with extended info"""
        # Given - create test agents
        async with self._create_agents(db_source, scaling_group, count=2) as agents:
            agent_ids = [agent.agent_id for agent in agents]

            # When
            querier = Querier(
                conditions=[AgentConditions.by_scaling_group(scaling_group)],
                orders=[AgentOrders.id(ascending=True)],
            )
            result = await agent_repository.list_extended_data(querier)

            # Then
            assert len(result) >= 2
            assert all(isinstance(agent, AgentDataExtended) for agent in result)
            assert all(agent.scaling_group == scaling_group for agent in result)
            result_ids = [agent.id for agent in result]
            for agent_id in agent_ids:
                assert agent_id in result_ids

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "status_filter",
        [
            [AgentStatus.ALIVE],
            [AgentStatus.ALIVE, AgentStatus.RESTARTING],
        ],
    )
    async def test_repository_list_extended_data_with_status(
        self,
        agent_repository: AgentRepository,
        db_source: AgentDBSource,
        scaling_group: str,
        status_filter: list[AgentStatus],
        mock_get_resource_slots: AsyncMock,
    ) -> None:
        """Test repository list_extended_data with different status filters"""
        # Given - create test agent
        async with self._create_agents(db_source, scaling_group, count=1) as agents:
            agent_id = agents[0].agent_id

            # When
            querier = Querier(
                conditions=[AgentConditions.by_statuses(status_filter)],
                orders=[],
            )
            result = await agent_repository.list_extended_data(querier)

            # Then
            assert len(result) >= 1
            assert all(agent.status in status_filter for agent in result)
            result_ids = [agent.id for agent in result]
            assert agent_id in result_ids

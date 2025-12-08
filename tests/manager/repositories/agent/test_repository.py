from collections.abc import AsyncGenerator, AsyncIterator, Generator, Mapping
from contextlib import asynccontextmanager as actxmgr
from dataclasses import dataclass
from datetime import datetime
from datetime import timezone as tz
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import sqlalchemy as sa

from ai.backend.common.auth import PublicKey
from ai.backend.common.clients.valkey_client.valkey_image.client import ValkeyImageClient
from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.clients.valkey_client.valkey_stat.client import ValkeyStatClient
from ai.backend.common.data.agent.types import AgentInfo
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
    AgentHeartbeatUpsert,
    AgentStatus,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.db_source.db_source import AgentDBSource
from ai.backend.manager.repositories.agent.options import AgentConditions, AgentOrders
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.base import OffsetPagination, Querier


@dataclass
class _SampleAgent:
    agent_id: AgentId
    heartbeat_upsert: AgentHeartbeatUpsert


class TestAgentRepository:
    @pytest.fixture
    async def agent_factory(self, db_source: AgentDBSource) -> AsyncGenerator[Any, None]:
        """Factory fixture for creating test agents with automatic cleanup."""
        created_agent_ids: list[AgentId] = []

        @actxmgr
        async def _create_agents(
            scaling_group: str,
            count: int = 1,
            **overrides: Any,
        ) -> AsyncIterator[list[_SampleAgent]]:
            """Create multiple test agents and yield them

            Args:
                scaling_group: Scaling group name for the agents
                count: Number of agents to create
                **overrides: Override default agent info attributes
            """
            agents: list[_SampleAgent] = []

            for i in range(count):
                agent_id = AgentId(f"agent-{uuid4().hex[:8]}")
                created_agent_ids.append(agent_id)

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
                    heartbeat_received=datetime.now(tz.utc),
                )

                await db_source.upsert_agent_with_state(heartbeat_upsert)
                agents.append(_SampleAgent(agent_id=agent_id, heartbeat_upsert=heartbeat_upsert))

            yield agents

        yield _create_agents

        # Cleanup all created agents
        # Delete in reverse order to handle dependencies and use individual try-catch
        async with db_source._db.begin_session() as db_session:
            for agent_id in reversed(created_agent_ids):
                try:
                    await db_session.execute(sa.delete(AgentRow).where(AgentRow.id == agent_id))
                except Exception:
                    # Ignore cleanup errors - agent might have been deleted by test
                    pass

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
            # Delete all agents in this scaling group first to avoid foreign key violations
            async with database_engine.begin_session() as db_session:
                await db_session.execute(
                    sa.delete(AgentRow).where(AgentRow.scaling_group == group_name)
                )
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

    @pytest.fixture
    async def single_agent(
        self, agent_factory: Any, scaling_group: str
    ) -> AsyncGenerator[_SampleAgent, None]:
        """Pre-created single agent for simple tests."""
        async with agent_factory(scaling_group, count=1) as agents:
            yield agents[0]

    @pytest.fixture
    async def two_agents(
        self, agent_factory: Any, scaling_group: str
    ) -> AsyncGenerator[list[_SampleAgent], None]:
        """Pre-created two agents for list/pagination tests."""
        async with agent_factory(scaling_group, count=2) as agents:
            yield agents

    @pytest.mark.asyncio
    async def test_db_source_search_agents_no_filter(
        self,
        db_source: AgentDBSource,
        single_agent: _SampleAgent,
    ) -> None:
        """Test searching agents without any filters"""
        # Given - single agent exists

        # When - search without filter
        querier = Querier(pagination=OffsetPagination(limit=10, offset=0))
        result = await db_source.search_agents(querier=querier)

        # Then - should find the agent
        assert len(result.items) >= 1
        assert any(agent.id == single_agent.agent_id for agent in result.items)

    @pytest.mark.asyncio
    async def test_db_source_search_agents_with_querier(
        self,
        db_source: AgentDBSource,
        single_agent: _SampleAgent,
    ) -> None:
        """Test searching agents with specific ID filter"""
        # Given - single agent exists

        # When - search with specific ID filter
        querier = Querier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[AgentConditions.by_id_equals(single_agent.agent_id)],
        )
        result = await db_source.search_agents(querier=querier)

        # Then - should find exactly that agent
        assert len(result.items) == 1
        assert result.items[0].id == single_agent.agent_id

    @pytest.fixture
    async def three_agents(
        self, agent_factory: Any, scaling_group: str
    ) -> AsyncGenerator[list[_SampleAgent], None]:
        """Pre-created three agents for ordering tests."""
        async with agent_factory(scaling_group, count=3) as agents:
            yield agents

    @pytest.mark.asyncio
    @pytest.mark.parametrize("ascending", [True, False])
    async def test_db_source_search_agents_order(
        self,
        db_source: AgentDBSource,
        three_agents: list[_SampleAgent],
        ascending: bool,
    ) -> None:
        """Test listing agents with different sort orders"""
        # Given - Querier with ordering by first_contact
        querier = Querier(
            pagination=OffsetPagination(limit=10, offset=0),
            orders=[AgentOrders.first_contact(ascending=ascending)],
        )

        # When - search with ordering
        result = await db_source.search_agents(querier=querier)

        # Then - should find all three agents in correct order
        assert len(result.items) >= 3
        agent_ids = [
            agent.id for agent in result.items if agent.id in [a.agent_id for a in three_agents]
        ]
        assert len(agent_ids) == 3

        # Verify ordering by checking first_contact timestamps
        first_contacts = [agent.first_contact for agent in result.items if agent.id in agent_ids]
        if ascending:
            assert first_contacts == sorted(first_contacts)
        else:
            assert first_contacts == sorted(first_contacts, reverse=True)

    @pytest.fixture
    async def five_agents(
        self, agent_factory: Any, scaling_group: str
    ) -> AsyncGenerator[list[_SampleAgent], None]:
        """Pre-created five agents for pagination tests."""
        async with agent_factory(scaling_group, count=5) as agents:
            yield agents

    @pytest.mark.asyncio
    async def test_db_source_list_agents_with_pagination(
        self,
        db_source: AgentDBSource,
        five_agents: list[_SampleAgent],
    ) -> None:
        """Test pagination works correctly with offset pagination"""
        # Given - five agents exist
        five_agent_ids = [agent.agent_id for agent in five_agents]

        # When - fetch first page with limit=2, offset=0
        querier_page1 = Querier(pagination=OffsetPagination(limit=2, offset=0))
        result_page1 = await db_source.search_agents(querier=querier_page1)

        # Then - should get 2 items and correct total_count
        page1_ids = [agent.id for agent in result_page1.items if agent.id in five_agent_ids]
        assert len(page1_ids) == 2
        assert result_page1.total_count >= 5

        # When - fetch second page with limit=2, offset=2
        querier_page2 = Querier(pagination=OffsetPagination(limit=2, offset=2))
        result_page2 = await db_source.search_agents(querier=querier_page2)

        # Then - should get 2 items with different agents
        page2_ids = [agent.id for agent in result_page2.items if agent.id in five_agent_ids]
        assert len(page2_ids) == 2
        assert result_page2.total_count >= 5

        # Verify pages contain different agents
        assert set(page1_ids).isdisjoint(set(page2_ids))

    @pytest.mark.asyncio
    async def test_search_agents(
        self,
        agent_repository: AgentRepository,
        two_agents: list[_SampleAgent],
    ) -> None:
        """Test repository-level search agents without filters"""
        # Given - two agents exist

        # When - search without filter
        querier = Querier(pagination=OffsetPagination(limit=10, offset=0))
        result = await agent_repository.search_agents(querier=querier)

        # Then - should find at least the two test agents
        assert len(result.items) >= 2
        test_agent_ids = [agent.agent_id for agent in two_agents]
        found_ids = [agent.id for agent in result.items if agent.id in test_agent_ids]
        assert len(found_ids) == 2

    @pytest.mark.parametrize(
        ("status_filter", "expected_min_count"),
        [
            ([AgentStatus.ALIVE], 1),
            ([AgentStatus.ALIVE, AgentStatus.TERMINATED], 1),
        ],
    )
    @pytest.mark.asyncio
    async def test_search_agents_with_status_filter(
        self,
        agent_repository: AgentRepository,
        single_agent: _SampleAgent,
        status_filter: list[AgentStatus],
        expected_min_count: int,
    ) -> None:
        """Test repository-level search with status filters"""
        # Given - single agent exists with ALIVE status

        # When - search with status filter
        querier = Querier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[AgentConditions.by_status_contains(status_filter)],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should find at least expected_min_count agents
        assert len(result.items) >= expected_min_count
        # Verify all returned agents have status in the filter
        for agent in result.items:
            assert agent.status in status_filter

    @pytest.mark.asyncio
    async def test_search_agents_empty_result(
        self,
        agent_repository: AgentRepository,
    ) -> None:
        """Test search with impossible filter returns empty result"""
        # Given - no specific agents

        # When - search with non-existent agent ID
        non_existent_id = AgentId("non-existent-agent-id-12345")
        querier = Querier(
            pagination=OffsetPagination(limit=10, offset=0),
            conditions=[AgentConditions.by_id_equals(non_existent_id)],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should return empty result
        assert len(result.items) == 0
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_search_agents_with_fields(
        self,
        agent_repository: AgentRepository,
        two_agents: list[_SampleAgent],
    ) -> None:
        """Test search returns agents with all fields populated"""
        # Given - two agents exist

        # When - search agents
        querier = Querier(pagination=OffsetPagination(limit=10, offset=0))
        result = await agent_repository.search_agents(querier=querier)

        # Then - should find agents with all fields
        test_agent_ids = [agent.agent_id for agent in two_agents]
        found_agents = [agent for agent in result.items if agent.id in test_agent_ids]
        assert len(found_agents) == 2

        # Verify all AgentData fields are populated
        for agent in found_agents:
            assert agent.id is not None
            assert agent.status is not None
            assert agent.available_slots is not None
            assert agent.compute_plugins is not None
            assert agent.scaling_group is not None

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

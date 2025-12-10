"""
Tests for AgentRepository query options (conditions and orders).
Tests the filter and ordering functionality with real database operations.
"""

from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from datetime import timezone as tz
from time import sleep
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
import sqlalchemy as sa

from ai.backend.common.auth import PublicKey
from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.types import (
    AgentId,
    DeviceName,
    ResourceSlot,
    SlotName,
    SlotTypes,
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
from ai.backend.manager.repositories.agent.options import (
    AgentConditions,
    AgentOrders,
)
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.base import (
    CursorBackwardPagination,
    CursorForwardPagination,
    OffsetPagination,
    Querier,
)


class TestAgentConditions:
    """Test cases for AgentConditions query builders"""

    # Fixtures

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database engine that auto-cleans agent data after each test"""
        yield database_engine

        # Cleanup all agent data after test
        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(AgentRow))

    @pytest.fixture
    async def scaling_group(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[str, None]:
        """Create test scaling group and return group name"""
        from uuid import uuid4

        group_name = f"test-sgroup-{uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            scaling_group_row = ScalingGroupRow(
                name=group_name,
                driver="test",
                scheduler="test",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(scaling_group_row)
            await db_sess.flush()

        try:
            yield group_name
        finally:
            # Cleanup
            async with db_with_cleanup.begin_session() as db_sess:
                await db_sess.execute(
                    sa.delete(AgentRow).where(AgentRow.scaling_group == group_name)
                )
                await db_sess.execute(
                    sa.delete(ScalingGroupRow).where(ScalingGroupRow.name == group_name)
                )

    @pytest.fixture
    async def db_source(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[AgentDBSource, None]:
        """Create AgentDBSource with database"""
        yield AgentDBSource(db=db_with_cleanup)

    @pytest.fixture
    async def agent_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[AgentRepository, None]:
        """Create AgentRepository instance with database (minimal setup for search tests)"""
        # For search tests, we only need the db connection
        # Other dependencies (valkey clients, config) are mocked or not needed
        from unittest.mock import MagicMock

        from ai.backend.manager.config.loader.legacy_etcd_loader import LegacyEtcdLoader
        from ai.backend.manager.config.provider import ManagerConfigProvider

        mock_provider = MagicMock(spec=ManagerConfigProvider)
        mock_legacy_loader = MagicMock(spec=LegacyEtcdLoader)
        mock_provider.legacy_etcd_config_loader = mock_legacy_loader

        # Create mock valkey clients
        mock_valkey_image = MagicMock()
        mock_valkey_live = MagicMock()
        mock_valkey_stat = MagicMock()

        repo = AgentRepository(
            db=db_with_cleanup,
            valkey_image=mock_valkey_image,
            valkey_live=mock_valkey_live,
            valkey_stat=mock_valkey_stat,
            config_provider=mock_provider,
        )
        yield repo

    @pytest.fixture
    async def sample_agents_for_filter(
        self,
        db_source: AgentDBSource,
        scaling_group: str,
    ) -> AsyncGenerator[list[AgentId], None]:
        """Create sample agents with various IDs, statuses, and schedulable values for filter testing.

        Creates 5 agents:
        - agent-alpha (ALIVE, schedulable=True)
        - agent-ALPHA (ALIVE, schedulable=True) - for case sensitivity test
        - agent-beta (TERMINATED, schedulable=False)
        - agent-gamma (ALIVE, schedulable=False)
        - agent-delta (LOST, schedulable=True)
        """
        agents_data = [
            ("agent-alpha", AgentStatus.ALIVE, True),
            ("agent-ALPHA", AgentStatus.ALIVE, True),
            ("agent-beta", AgentStatus.TERMINATED, False),
            ("agent-gamma", AgentStatus.ALIVE, False),
            ("agent-delta", AgentStatus.LOST, True),
        ]

        agent_ids = []

        for agent_id_str, status, schedulable in agents_data:
            agent_id = AgentId(agent_id_str)
            agent_ids.append(agent_id)

            agent_info = AgentInfo(
                ip=f"192.168.1.{len(agent_ids)}",
                version="24.12.0",
                scaling_group=scaling_group,
                available_resource_slots=ResourceSlot({
                    SlotName("cpu"): "8",
                    SlotName("mem"): "32768",
                }),
                slot_key_and_units={
                    SlotName("cpu"): SlotTypes.COUNT,
                    SlotName("mem"): SlotTypes.BYTES,
                },
                compute_plugins={DeviceName("cpu"): {"brand": "Intel"}},
                addr=f"tcp://192.168.1.{len(agent_ids)}:6001",
                public_key=PublicKey(f"key-{agent_id_str}".encode()),
                public_host=f"192.168.1.{len(agent_ids)}",
                images=b"\x82\xc4\x00\x00",
                region="us-west-1",
                architecture="x86_64",
                auto_terminate_abusing_kernel=False,
            )

            heartbeat_upsert = AgentHeartbeatUpsert.from_agent_info(
                agent_id=agent_id,
                agent_info=agent_info,
                heartbeat_received=datetime.now(tz.utc),
            )

            # Manually set status and schedulable after creation
            await db_source.upsert_agent_with_state(heartbeat_upsert)

            # Update status and schedulable in DB
            async with db_source._db.begin_session() as db_sess:
                await db_sess.execute(
                    sa.update(AgentRow)
                    .where(AgentRow.id == agent_id)
                    .values(status=status, schedulable=schedulable)
                )

        yield agent_ids

    # AgentConditions Tests - by_id

    @pytest.mark.asyncio
    async def test_agent_by_id_contains_case_sensitive(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_filter: list[AgentId],
    ) -> None:
        """Test case-sensitive ID contains filter"""
        # Given - agents with IDs: agent-alpha, agent-ALPHA, agent-beta, agent-gamma, agent-delta

        # When - search for "alpha" case-sensitively
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[AgentConditions.by_id_contains("alpha", case_insensitive=False)],
            orders=[],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should match "agent-alpha" only, not "agent-ALPHA"
        assert len(result.items) == 1
        assert result.items[0].id == AgentId("agent-alpha")

    @pytest.mark.asyncio
    async def test_agent_by_id_contains_case_insensitive(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_filter: list[AgentId],
    ) -> None:
        """Test case-insensitive ID contains filter"""
        # Given - agents with IDs: agent-alpha, agent-ALPHA, agent-beta, agent-gamma, agent-delta

        # When - search for "alpha" case-insensitively
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[AgentConditions.by_id_contains("alpha", case_insensitive=True)],
            orders=[],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should match both "agent-alpha" and "agent-ALPHA"
        assert len(result.items) == 2
        agent_ids = {agent.id for agent in result.items}
        assert agent_ids == {AgentId("agent-alpha"), AgentId("agent-ALPHA")}

    @pytest.mark.asyncio
    async def test_agent_by_id_equals_case_sensitive(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_filter: list[AgentId],
    ) -> None:
        """Test case-sensitive ID equals filter"""
        # Given - agents with IDs: agent-alpha, agent-ALPHA, agent-beta, agent-gamma, agent-delta

        # When - search for exact "agent-alpha" case-sensitively
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[AgentConditions.by_id_equals("agent-alpha", case_insensitive=False)],
            orders=[],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should match exactly "agent-alpha"
        assert len(result.items) == 1
        assert result.items[0].id == AgentId("agent-alpha")

    @pytest.mark.asyncio
    async def test_agent_by_id_equals_case_insensitive(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_filter: list[AgentId],
    ) -> None:
        """Test case-insensitive ID equals filter"""
        # Given - agents with IDs: agent-alpha, agent-ALPHA, agent-beta, agent-gamma, agent-delta

        # When - search for "agent-alpha" case-insensitively
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[AgentConditions.by_id_equals("agent-alpha", case_insensitive=True)],
            orders=[],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should match both "agent-alpha" and "agent-ALPHA"
        assert len(result.items) == 2
        agent_ids = {agent.id for agent in result.items}
        assert agent_ids == {AgentId("agent-alpha"), AgentId("agent-ALPHA")}

    # AgentConditions Tests - by_status

    @pytest.mark.asyncio
    async def test_agent_by_status_contains_multiple(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_filter: list[AgentId],
    ) -> None:
        """Test filtering by multiple statuses"""
        # Given - agents with ALIVE (3), TERMINATED (1), LOST (1) statuses

        # When - search for ALIVE or TERMINATED
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[
                AgentConditions.by_status_contains([AgentStatus.ALIVE, AgentStatus.TERMINATED])
            ],
            orders=[],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should find 4 agents (3 ALIVE + 1 TERMINATED)
        assert len(result.items) == 4
        assert all(
            agent.status in [AgentStatus.ALIVE, AgentStatus.TERMINATED] for agent in result.items
        )

    @pytest.mark.asyncio
    async def test_agent_by_status_contains_single(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_filter: list[AgentId],
    ) -> None:
        """Test filtering by single status in a list"""
        # Given - agents with ALIVE (3), TERMINATED (1), LOST (1) statuses

        # When - search for LOST only
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[AgentConditions.by_status_contains([AgentStatus.LOST])],
            orders=[],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should find 1 agent (agent-delta)
        assert len(result.items) == 1
        assert result.items[0].status == AgentStatus.LOST
        assert result.items[0].id == AgentId("agent-delta")

    @pytest.mark.asyncio
    async def test_agent_by_status_equals(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_filter: list[AgentId],
    ) -> None:
        """Test filtering by exact status"""
        # Given - agents with ALIVE (3), TERMINATED (1), LOST (1) statuses

        # When - search for TERMINATED status
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[AgentConditions.by_status_equals(AgentStatus.TERMINATED)],
            orders=[],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should find 1 agent (agent-beta)
        assert len(result.items) == 1
        assert result.items[0].status == AgentStatus.TERMINATED
        assert result.items[0].id == AgentId("agent-beta")

    # AgentConditions Tests - by_schedulable

    @pytest.mark.asyncio
    async def test_agent_by_schedulable_true(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_filter: list[AgentId],
    ) -> None:
        """Test filtering by schedulable=True"""
        # Given - agents with schedulable: True (3), False (2)

        # When - search for schedulable agents only
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[AgentConditions.by_schedulable(True)],
            orders=[],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should find 3 agents (agent-alpha, agent-ALPHA, agent-delta)
        assert len(result.items) == 3
        assert all(agent.schedulable is True for agent in result.items)
        agent_ids = {agent.id for agent in result.items}
        assert agent_ids == {
            AgentId("agent-alpha"),
            AgentId("agent-ALPHA"),
            AgentId("agent-delta"),
        }

    @pytest.mark.asyncio
    async def test_agent_by_schedulable_false(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_filter: list[AgentId],
    ) -> None:
        """Test filtering by schedulable=False"""
        # Given - agents with schedulable: True (3), False (2)

        # When - search for non-schedulable agents only
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[AgentConditions.by_schedulable(False)],
            orders=[],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should find 2 agents (agent-beta, agent-gamma)
        assert len(result.items) == 2
        assert all(agent.schedulable is False for agent in result.items)
        agent_ids = {agent.id for agent in result.items}
        assert agent_ids == {AgentId("agent-beta"), AgentId("agent-gamma")}

    # Edge Cases

    @pytest.mark.asyncio
    async def test_agent_no_match_returns_empty(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_filter: list[AgentId],
    ) -> None:
        """Test that searching for non-existent agent returns empty with total_count=0"""
        # Given - agents with known IDs

        # When - search for non-existent agent ID
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[AgentConditions.by_id_equals("nonexistent-agent-id")],
            orders=[],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should return empty result
        assert len(result.items) == 0
        assert result.total_count == 0


class TestAgentOrders:
    """Test cases for AgentOrders query builders"""

    # Fixtures

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database engine that auto-cleans agent data after each test"""
        yield database_engine

        # Cleanup all agent data after test
        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(AgentRow))

    @pytest.fixture
    async def two_scaling_groups(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[tuple[str, str], None]:
        """Create two test scaling groups with predictable alphabetical order"""
        group1 = f"sgroup-alpha-{uuid4().hex[:8]}"
        group2 = f"sgroup-beta-{uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            for group_name in [group1, group2]:
                scaling_group_row = ScalingGroupRow(
                    name=group_name,
                    driver="test",
                    scheduler="test",
                    scheduler_opts=ScalingGroupOpts(),
                )
                db_sess.add(scaling_group_row)
            await db_sess.flush()

        try:
            yield (group1, group2)
        finally:
            # Cleanup
            async with db_with_cleanup.begin_session() as db_sess:
                await db_sess.execute(
                    sa.delete(AgentRow).where(AgentRow.scaling_group.in_([group1, group2]))
                )
                await db_sess.execute(
                    sa.delete(ScalingGroupRow).where(ScalingGroupRow.name.in_([group1, group2]))
                )

    @pytest.fixture
    async def db_source(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[AgentDBSource, None]:
        """Create AgentDBSource with database"""
        yield AgentDBSource(db=db_with_cleanup)

    @pytest.fixture
    async def agent_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[AgentRepository, None]:
        """Create AgentRepository instance with database"""
        mock_provider = MagicMock(spec=ManagerConfigProvider)
        mock_legacy_loader = MagicMock(spec=LegacyEtcdLoader)
        mock_provider.legacy_etcd_config_loader = mock_legacy_loader

        # Create mock valkey clients
        mock_valkey_image = MagicMock()
        mock_valkey_live = MagicMock()
        mock_valkey_stat = MagicMock()

        repo = AgentRepository(
            db=db_with_cleanup,
            valkey_image=mock_valkey_image,
            valkey_live=mock_valkey_live,
            valkey_stat=mock_valkey_stat,
            config_provider=mock_provider,
        )
        yield repo

    @pytest.fixture
    async def sample_agents_for_order(
        self,
        db_source: AgentDBSource,
        two_scaling_groups: tuple[str, str],
    ) -> AsyncGenerator[list[tuple[AgentId, dict]], None]:
        """Create 4 agents with predictable ordering values.

        Returns:
            List of tuples (agent_id, metadata) where metadata contains:
            - index: creation order (0-3)
            - scaling_group: assigned scaling group
            - schedulable: True/False

        This metadata helps verify ordering without hardcoding agent IDs.
        """
        group1, group2 = two_scaling_groups

        # Generate unique random suffix for this test run
        run_id = uuid4().hex[:8]

        agents_data = [
            (f"agent-order-1-{run_id}", group1, True),  # oldest, group1, schedulable
            (f"agent-order-2-{run_id}", group2, False),  # 2nd oldest, group2, not schedulable
            (f"agent-order-3-{run_id}", group1, True),  # 2nd newest, group1, schedulable
            (f"agent-order-4-{run_id}", group2, False),  # newest, group2, not schedulable
        ]

        created_agents = []

        for idx, (agent_id_str, scaling_group, schedulable) in enumerate(agents_data):
            agent_id = AgentId(agent_id_str)

            agent_info = AgentInfo(
                ip=f"192.168.1.{idx + 100}",  # Start from .100 to avoid conflicts
                version="24.12.0",
                scaling_group=scaling_group,
                available_resource_slots=ResourceSlot({
                    SlotName("cpu"): "8",
                    SlotName("mem"): "32768",
                }),
                slot_key_and_units={
                    SlotName("cpu"): SlotTypes.COUNT,
                    SlotName("mem"): SlotTypes.BYTES,
                },
                compute_plugins={DeviceName("cpu"): {"brand": "Intel"}},
                addr=f"tcp://192.168.1.{idx + 100}:6001",
                public_key=PublicKey(f"key-{agent_id_str}".encode()),
                public_host=f"192.168.1.{idx + 100}",
                images=b"\x82\xc4\x00\x00",
                region="us-west-1",
                architecture="x86_64",
                auto_terminate_abusing_kernel=False,
            )

            heartbeat_upsert = AgentHeartbeatUpsert.from_agent_info(
                agent_id=agent_id,
                agent_info=agent_info,
                heartbeat_received=datetime.now(tz.utc),
            )

            await db_source.upsert_agent_with_state(heartbeat_upsert)

            # Update schedulable in DB
            async with db_source._db.begin_session() as db_sess:
                await db_sess.execute(
                    sa.update(AgentRow)
                    .where(AgentRow.id == agent_id)
                    .values(schedulable=schedulable)
                )

            # Store metadata for verification
            created_agents.append((
                agent_id,
                {
                    "index": idx,
                    "scaling_group": scaling_group,
                    "schedulable": schedulable,
                },
            ))

            # Small delay to ensure different first_contact timestamps
            if idx < len(agents_data) - 1:
                sleep(0.1)

        yield created_agents

    # AgentOrders Tests - by ID

    @pytest.mark.asyncio
    async def test_agent_order_by_id_ascending(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_order: list[tuple[AgentId, dict]],
    ) -> None:
        """Test ordering agents by ID in ascending order"""
        # Given - 4 agents with sequential IDs (agent-order-1-xxx, 2, 3, 4)

        # When - order by ID ascending
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[AgentOrders.id(ascending=True)],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should be ordered by creation index (1, 2, 3, 4)
        # Filter to only our test agents
        test_agent_ids = {agent_id for agent_id, _ in sample_agents_for_order}
        test_results = [agent for agent in result.items if agent.id in test_agent_ids]

        assert len(test_results) == 4
        # Verify they're in ascending order
        for i in range(len(test_results) - 1):
            assert test_results[i].id < test_results[i + 1].id

    @pytest.mark.asyncio
    async def test_agent_order_by_id_descending(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_order: list[tuple[AgentId, dict]],
    ) -> None:
        """Test ordering agents by ID in descending order"""
        # Given - 4 agents with sequential IDs (agent-order-1-xxx, 2, 3, 4)

        # When - order by ID descending
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[AgentOrders.id(ascending=False)],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should be ordered in reverse
        # Filter to only our test agents
        test_agent_ids = {agent_id for agent_id, _ in sample_agents_for_order}
        test_results = [agent for agent in result.items if agent.id in test_agent_ids]

        assert len(test_results) == 4
        # Verify they're in descending order
        for i in range(len(test_results) - 1):
            assert test_results[i].id > test_results[i + 1].id

    # AgentOrders Tests - by Scaling Group

    @pytest.mark.asyncio
    async def test_agent_order_by_scaling_group_ascending(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_order: list[tuple[AgentId, dict]],
        two_scaling_groups: tuple[str, str],
    ) -> None:
        """Test ordering agents by scaling group in ascending order"""
        # Given - 4 agents in alternating groups (group1, group2, group1, group2)
        group1, group2 = two_scaling_groups

        # When - order by scaling_group ascending
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[AgentOrders.scaling_group(ascending=True)],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - groups should be ordered
        test_agent_ids = {agent_id for agent_id, _ in sample_agents_for_order}
        test_results = [agent for agent in result.items if agent.id in test_agent_ids]

        assert len(test_results) == 4

        # Group results by scaling_group
        groups = [agent.scaling_group for agent in test_results]
        # Verify groups are in ascending order
        assert groups == sorted(groups)

    @pytest.mark.asyncio
    async def test_agent_order_by_scaling_group_descending(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_order: list[tuple[AgentId, dict]],
        two_scaling_groups: tuple[str, str],
    ) -> None:
        """Test ordering agents by scaling group in descending order"""
        # Given - 4 agents in alternating groups
        group1, group2 = two_scaling_groups

        # When - order by scaling_group descending
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[AgentOrders.scaling_group(ascending=False)],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - groups should be in reverse order
        test_agent_ids = {agent_id for agent_id, _ in sample_agents_for_order}
        test_results = [agent for agent in result.items if agent.id in test_agent_ids]

        assert len(test_results) == 4

        # Group results by scaling_group
        groups = [agent.scaling_group for agent in test_results]
        # Verify groups are in descending order
        assert groups == sorted(groups, reverse=True)

    # AgentOrders Tests - by First Contact

    @pytest.mark.asyncio
    async def test_agent_order_by_first_contact_ascending(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_order: list[tuple[AgentId, dict]],
    ) -> None:
        """Test ordering agents by first_contact (oldest first)"""
        # Given - 4 agents created with delays (index 0 oldest → index 3 newest)

        # When - order by first_contact ascending
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[AgentOrders.first_contact(ascending=True)],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should be chronologically ordered (oldest first)
        test_agent_ids = {agent_id for agent_id, _ in sample_agents_for_order}
        test_results = [agent for agent in result.items if agent.id in test_agent_ids]

        assert len(test_results) == 4
        # Verify chronological order
        for i in range(len(test_results) - 1):
            assert test_results[i].first_contact <= test_results[i + 1].first_contact

    @pytest.mark.asyncio
    async def test_agent_order_by_first_contact_descending(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_order: list[tuple[AgentId, dict]],
    ) -> None:
        """Test ordering agents by first_contact (newest first)"""
        # Given - 4 agents created with delays

        # When - order by first_contact descending
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[AgentOrders.first_contact(ascending=False)],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - should be in reverse chronological order (newest first)
        test_agent_ids = {agent_id for agent_id, _ in sample_agents_for_order}
        test_results = [agent for agent in result.items if agent.id in test_agent_ids]

        assert len(test_results) == 4
        # Verify reverse chronological order
        for i in range(len(test_results) - 1):
            assert test_results[i].first_contact >= test_results[i + 1].first_contact

    # AgentOrders Tests - by Schedulable

    @pytest.mark.asyncio
    async def test_agent_order_by_schedulable_ascending(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_order: list[tuple[AgentId, dict]],
    ) -> None:
        """Test ordering agents by schedulable (False first)"""
        # Given - 4 agents: indices 0,2 schedulable=True; 1,3 schedulable=False

        # When - order by schedulable ascending (False < True)
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[AgentOrders.schedulable(ascending=True)],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - False values should come first
        test_agent_ids = {agent_id for agent_id, _ in sample_agents_for_order}
        test_results = [agent for agent in result.items if agent.id in test_agent_ids]

        assert len(test_results) == 4

        # Count False and True
        false_count = sum(1 for agent in test_results if not agent.schedulable)
        true_count = sum(1 for agent in test_results if agent.schedulable)
        assert false_count == 2
        assert true_count == 2

        # Verify False comes before True
        schedulable_values = [agent.schedulable for agent in test_results]
        # All False should come before all True
        first_true_index = schedulable_values.index(True)
        assert all(not v for v in schedulable_values[:first_true_index])
        assert all(v for v in schedulable_values[first_true_index:])

    @pytest.mark.asyncio
    async def test_agent_order_by_schedulable_descending(
        self,
        agent_repository: AgentRepository,
        sample_agents_for_order: list[tuple[AgentId, dict]],
    ) -> None:
        """Test ordering agents by schedulable (True first)"""
        # Given - 4 agents: indices 0,2 schedulable=True; 1,3 schedulable=False

        # When - order by schedulable descending (True > False)
        querier = Querier(
            pagination=OffsetPagination(limit=100, offset=0),
            conditions=[],
            orders=[AgentOrders.schedulable(ascending=False)],
        )
        result = await agent_repository.search_agents(querier=querier)

        # Then - True values should come first
        test_agent_ids = {agent_id for agent_id, _ in sample_agents_for_order}
        test_results = [agent for agent in result.items if agent.id in test_agent_ids]

        assert len(test_results) == 4

        # Count False and True
        false_count = sum(1 for agent in test_results if not agent.schedulable)
        true_count = sum(1 for agent in test_results if agent.schedulable)
        assert false_count == 2
        assert true_count == 2

        # Verify True comes before False
        schedulable_values = [agent.schedulable for agent in test_results]
        # All True should come before all False
        first_false_index = schedulable_values.index(False)
        assert all(v for v in schedulable_values[:first_false_index])
        assert all(not v for v in schedulable_values[first_false_index:])


class TestAgentCursorPagination:
    """Test cases for cursor-based pagination with agents.

    Validates that forward/backward cursor pagination works correctly:
    - Forward (first/after): DESC order, newest first, next page shows older items
    - Backward (last/before): ASC order, fetches older items (reversed for display)
    """

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database engine that auto-cleans agent data after each test"""
        yield database_engine

        # Cleanup all agent data after test
        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(AgentRow))

    @pytest.fixture
    async def scaling_group(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[str, None]:
        """Create test scaling group and return group name"""
        group_name = f"test-sgroup-cursor-{uuid4().hex[:8]}"

        async with db_with_cleanup.begin_session() as db_sess:
            scaling_group_row = ScalingGroupRow(
                name=group_name,
                driver="test",
                scheduler="test",
                scheduler_opts=ScalingGroupOpts(),
            )
            db_sess.add(scaling_group_row)
            await db_sess.flush()

        try:
            yield group_name
        finally:
            # Cleanup
            async with db_with_cleanup.begin_session() as db_sess:
                await db_sess.execute(
                    sa.delete(AgentRow).where(AgentRow.scaling_group == group_name)
                )
                await db_sess.execute(
                    sa.delete(ScalingGroupRow).where(ScalingGroupRow.name == group_name)
                )

    @pytest.fixture
    async def db_source(
        self, db_with_cleanup: ExtendedAsyncSAEngine
    ) -> AsyncGenerator[AgentDBSource, None]:
        """Create AgentDBSource with database"""
        yield AgentDBSource(db=db_with_cleanup)

    @pytest.fixture
    async def agent_repository(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[AgentRepository, None]:
        """Create AgentRepository instance with database"""
        mock_provider = MagicMock(spec=ManagerConfigProvider)
        mock_legacy_loader = MagicMock(spec=LegacyEtcdLoader)
        mock_provider.legacy_etcd_config_loader = mock_legacy_loader

        # Create mock valkey clients
        mock_valkey_image = MagicMock()
        mock_valkey_live = MagicMock()
        mock_valkey_stat = MagicMock()

        repo = AgentRepository(
            db=db_with_cleanup,
            valkey_image=mock_valkey_image,
            valkey_live=mock_valkey_live,
            valkey_stat=mock_valkey_stat,
            config_provider=mock_provider,
        )
        yield repo

    @pytest.fixture
    async def agents_for_cursor_pagination(
        self,
        db_source: AgentDBSource,
        scaling_group: str,
    ) -> AsyncGenerator[list[AgentId], None]:
        """Create 5 agents with distinct first_contact times for cursor pagination testing.

        Created order (oldest to newest): Agent-1, Agent-2, Agent-3, Agent-4, Agent-5
        Using explicit datetime values for predictable cursor pagination.
        """
        run_id = uuid4().hex[:8]
        base_time = datetime.now(tz.utc)

        agent_ids = []

        for i in range(1, 6):
            agent_id = AgentId(f"agent-cursor-{i}-{run_id}")
            agent_ids.append(agent_id)

            agent_info = AgentInfo(
                ip=f"192.168.1.{i + 200}",  # Start from .201 to avoid conflicts
                version="24.12.0",
                scaling_group=scaling_group,
                available_resource_slots=ResourceSlot({
                    SlotName("cpu"): "8",
                    SlotName("mem"): "32768",
                }),
                slot_key_and_units={
                    SlotName("cpu"): SlotTypes.COUNT,
                    SlotName("mem"): SlotTypes.BYTES,
                },
                compute_plugins={DeviceName("cpu"): {"brand": "Intel"}},
                addr=f"tcp://192.168.1.{i + 200}:6001",
                public_key=PublicKey(f"key-cursor-{i}-{run_id}".encode()),
                public_host=f"192.168.1.{i + 200}",
                images=b"\x82\xc4\x00\x00",
                region="us-west-1",
                architecture="x86_64",
                auto_terminate_abusing_kernel=False,
            )

            # Agent-1 oldest, Agent-5 newest
            heartbeat_time = base_time - timedelta(days=5 - i)

            heartbeat_upsert = AgentHeartbeatUpsert.from_agent_info(
                agent_id=agent_id,
                agent_info=agent_info,
                heartbeat_received=heartbeat_time,
            )

            await db_source.upsert_agent_with_state(heartbeat_upsert)

        yield agent_ids

    # Cursor Pagination Tests

    @pytest.mark.asyncio
    async def test_forward_pagination_first_page_shows_newest_first(
        self,
        agent_repository: AgentRepository,
        agents_for_cursor_pagination: list[AgentId],
    ) -> None:
        """Test forward pagination first page shows newest agents first (DESC order).

        With 5 agents (oldest to newest: Agent-1 to Agent-5),
        first page with first=3 should return: Agent-5, Agent-4, Agent-3
        """
        querier = Querier(
            pagination=CursorForwardPagination(
                first=3,
                cursor_order=AgentOrders.first_contact(ascending=False),  # DESC
                cursor_condition=None,  # No cursor = first page
            ),
        )
        result = await agent_repository.search_agents(querier=querier)

        # Filter to only our test agents
        test_agent_ids = set(agents_for_cursor_pagination)
        test_results = [agent for agent in result.items if agent.id in test_agent_ids]

        assert len(test_results) == 3
        # Should be newest first (Agent-5, 4, 3)
        assert "agent-cursor-5-" in test_results[0].id
        assert "agent-cursor-4-" in test_results[1].id
        assert "agent-cursor-3-" in test_results[2].id
        assert result.has_previous_page is False  # First page
        assert result.has_next_page is True  # More items exist

    @pytest.mark.asyncio
    async def test_forward_pagination_with_cursor_shows_older_items(
        self,
        agent_repository: AgentRepository,
        agents_for_cursor_pagination: list[AgentId],
    ) -> None:
        """Test forward pagination with cursor shows older agents (next page).

        After viewing Agent-5, Agent-4, Agent-3 (first page),
        using Agent-3's cursor should return: Agent-2, Agent-1
        """
        # Get Agent-3's ID for cursor
        agent_3_id = [aid for aid in agents_for_cursor_pagination if "agent-cursor-3-" in aid][0]

        # Forward cursor condition: first_contact < cursor's first_contact
        cursor_condition = AgentConditions.by_cursor_forward(agent_3_id)

        querier = Querier(
            pagination=CursorForwardPagination(
                first=3,
                cursor_order=AgentOrders.first_contact(ascending=False),  # DESC
                cursor_condition=cursor_condition,
            ),
        )
        result = await agent_repository.search_agents(querier=querier)

        # Filter to only our test agents
        test_agent_ids = set(agents_for_cursor_pagination)
        test_results = [agent for agent in result.items if agent.id in test_agent_ids]

        # Should return older items (Agent-2, Agent-1)
        assert len(test_results) == 2
        assert "agent-cursor-2-" in test_results[0].id
        assert "agent-cursor-1-" in test_results[1].id
        assert result.has_previous_page is True  # Has items before (cursor was provided)
        assert result.has_next_page is False  # No more items

    @pytest.mark.asyncio
    async def test_backward_pagination_last_page_fetches_oldest_first(
        self,
        agent_repository: AgentRepository,
        agents_for_cursor_pagination: list[AgentId],
    ) -> None:
        """Test backward pagination without cursor fetches from the end (oldest first in DB order).

        With 5 agents, last=3 without cursor should fetch the 3 oldest items
        in ASC order: Agent-1, Agent-2, Agent-3
        """
        querier = Querier(
            pagination=CursorBackwardPagination(
                last=3,
                cursor_order=AgentOrders.first_contact(ascending=True),  # ASC
                cursor_condition=None,  # No cursor = last page
            ),
        )
        result = await agent_repository.search_agents(querier=querier)

        # Filter to only our test agents
        test_agent_ids = set(agents_for_cursor_pagination)
        test_results = [agent for agent in result.items if agent.id in test_agent_ids]

        # Backward pagination returns in ascending order (oldest first in this slice)
        # These are the 3 oldest items: Agent-1, Agent-2, Agent-3
        assert len(test_results) == 3
        assert "agent-cursor-1-" in test_results[0].id
        assert "agent-cursor-2-" in test_results[1].id
        assert "agent-cursor-3-" in test_results[2].id
        assert result.has_previous_page is True  # More items exist before
        assert result.has_next_page is False  # No cursor = last page

    @pytest.mark.asyncio
    async def test_backward_pagination_with_cursor_shows_newer_items(
        self,
        agent_repository: AgentRepository,
        agents_for_cursor_pagination: list[AgentId],
    ) -> None:
        """Test backward pagination with cursor shows newer agents (previous page).

        If we're at Agent-1, Agent-2, Agent-3 and go back (before Agent-3),
        we should get Agent-4, Agent-5 (items newer than the current view).
        """
        # Get Agent-3's ID for cursor
        agent_3_id = [aid for aid in agents_for_cursor_pagination if "agent-cursor-3-" in aid][0]

        # Backward cursor condition: first_contact > cursor's first_contact
        cursor_condition = AgentConditions.by_cursor_backward(agent_3_id)

        querier = Querier(
            pagination=CursorBackwardPagination(
                last=3,
                cursor_order=AgentOrders.first_contact(ascending=True),  # ASC
                cursor_condition=cursor_condition,
            ),
        )
        result = await agent_repository.search_agents(querier=querier)

        # Filter to only our test agents
        test_agent_ids = set(agents_for_cursor_pagination)
        test_results = [agent for agent in result.items if agent.id in test_agent_ids]

        # Should return newer items (Agent-4, Agent-5) in ASC order
        assert len(test_results) == 2
        assert "agent-cursor-4-" in test_results[0].id
        assert "agent-cursor-5-" in test_results[1].id
        assert result.has_previous_page is False  # No more newer items
        assert result.has_next_page is True  # Has items after (cursor was provided)

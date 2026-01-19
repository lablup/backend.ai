"""
Tests for calculate_total_resource_slots_by_scaling_group method in ScheduleDBSource.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from ai.backend.common.types import AgentId, ResourceSlot
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.keypair import KeyPairRow
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.resource_policy import (
    KeyPairResourcePolicyRow,
    ProjectResourcePolicyRow,
    UserResourcePolicyRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.scheduler.db_source.db_source import ScheduleDBSource
from ai.backend.testutils.db import with_tables


@dataclass
class ScalingGroupFixtureData:
    name: str


@dataclass
class AgentFixtureData:
    id: str
    scaling_group: str
    available_slots: dict[str, Decimal]


class TestCalculateTotalResourceSlotsByScalingGroup:
    """Tests for calculate_total_resource_slots_by_scaling_group method."""

    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database with required tables for testing."""
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ScalingGroupRow,
                UserResourcePolicyRow,
                ProjectResourcePolicyRow,
                KeyPairResourcePolicyRow,
                UserRoleRow,
                UserRow,
                KeyPairRow,
                GroupRow,
                ImageRow,
                SessionRow,
                AgentRow,
                KernelRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    async def domain(self, db_with_tables: ExtendedAsyncSAEngine) -> None:
        """Create a domain (FK dependency)."""
        async with db_with_tables.begin_session() as sess:
            sess.add(
                DomainRow(
                    name="default",
                    description="Test domain",
                    is_active=True,
                    total_resource_slots={},
                )
            )
            await sess.flush()

    @pytest.fixture
    async def scaling_group(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        domain: None,
    ) -> ScalingGroupFixtureData:
        """Create a scaling group."""
        name = f"sg-{uuid.uuid4().hex[:8]}"
        async with db_with_tables.begin_session() as sess:
            sess.add(
                ScalingGroupRow(
                    name=name,
                    description=f"Test scaling group {name}",
                    is_active=True,
                    is_public=True,
                    driver="static",
                    scheduler="fifo",
                    driver_opts={},
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            await sess.flush()
        return ScalingGroupFixtureData(name=name)

    @pytest.fixture
    async def scaling_group2(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        domain: None,
    ) -> ScalingGroupFixtureData:
        """Create a second scaling group."""
        name = f"sg2-{uuid.uuid4().hex[:8]}"
        async with db_with_tables.begin_session() as sess:
            sess.add(
                ScalingGroupRow(
                    name=name,
                    description=f"Test scaling group {name}",
                    is_active=True,
                    is_public=True,
                    driver="static",
                    scheduler="fifo",
                    driver_opts={},
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
            await sess.flush()
        return ScalingGroupFixtureData(name=name)

    @pytest.fixture
    async def agent(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        scaling_group: ScalingGroupFixtureData,
    ) -> AgentFixtureData:
        """Create an ALIVE, schedulable agent with 4 CPU, 8GB mem."""
        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        available_slots: dict[str, Decimal] = {"cpu": Decimal("4"), "mem": Decimal("8589934592")}
        async with db_with_tables.begin_session() as sess:
            sess.add(
                AgentRow(
                    id=AgentId(agent_id),
                    status=AgentStatus.ALIVE,
                    region="local",
                    scaling_group=scaling_group.name,
                    available_slots=ResourceSlot(available_slots),
                    occupied_slots=ResourceSlot({}),
                    addr="tcp://127.0.0.1:5001",
                    first_contact=datetime.now(UTC),
                    lost_at=None,
                    version="24.03.0",
                    architecture="x86_64",
                    compute_plugins={},
                    schedulable=True,
                )
            )
            await sess.flush()
        return AgentFixtureData(
            id=agent_id, scaling_group=scaling_group.name, available_slots=available_slots
        )

    @pytest.fixture
    async def agent2(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        scaling_group: ScalingGroupFixtureData,
    ) -> AgentFixtureData:
        """Create a second ALIVE, schedulable agent with 8 CPU, 16GB mem."""
        agent_id = f"agent2-{uuid.uuid4().hex[:8]}"
        available_slots: dict[str, Decimal] = {"cpu": Decimal("8"), "mem": Decimal("17179869184")}
        async with db_with_tables.begin_session() as sess:
            sess.add(
                AgentRow(
                    id=AgentId(agent_id),
                    status=AgentStatus.ALIVE,
                    region="local",
                    scaling_group=scaling_group.name,
                    available_slots=ResourceSlot(available_slots),
                    occupied_slots=ResourceSlot({}),
                    addr="tcp://127.0.0.1:5002",
                    first_contact=datetime.now(UTC),
                    lost_at=None,
                    version="24.03.0",
                    architecture="x86_64",
                    compute_plugins={},
                    schedulable=True,
                )
            )
            await sess.flush()
        return AgentFixtureData(
            id=agent_id, scaling_group=scaling_group.name, available_slots=available_slots
        )

    @pytest.fixture
    async def terminated_agent(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        scaling_group: ScalingGroupFixtureData,
    ) -> AgentFixtureData:
        """Create a TERMINATED agent."""
        agent_id = f"agent-terminated-{uuid.uuid4().hex[:8]}"
        available_slots: dict[str, Decimal] = {"cpu": Decimal("8")}
        async with db_with_tables.begin_session() as sess:
            sess.add(
                AgentRow(
                    id=AgentId(agent_id),
                    status=AgentStatus.TERMINATED,
                    region="local",
                    scaling_group=scaling_group.name,
                    available_slots=ResourceSlot(available_slots),
                    occupied_slots=ResourceSlot({}),
                    addr="tcp://127.0.0.1:5003",
                    first_contact=datetime.now(UTC),
                    lost_at=None,
                    version="24.03.0",
                    architecture="x86_64",
                    compute_plugins={},
                    schedulable=True,
                )
            )
            await sess.flush()
        return AgentFixtureData(
            id=agent_id, scaling_group=scaling_group.name, available_slots=available_slots
        )

    @pytest.fixture
    async def non_schedulable_agent(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        scaling_group: ScalingGroupFixtureData,
    ) -> AgentFixtureData:
        """Create a non-schedulable agent."""
        agent_id = f"agent-non-sched-{uuid.uuid4().hex[:8]}"
        available_slots: dict[str, Decimal] = {"cpu": Decimal("8")}
        async with db_with_tables.begin_session() as sess:
            sess.add(
                AgentRow(
                    id=AgentId(agent_id),
                    status=AgentStatus.ALIVE,
                    region="local",
                    scaling_group=scaling_group.name,
                    available_slots=ResourceSlot(available_slots),
                    occupied_slots=ResourceSlot({}),
                    addr="tcp://127.0.0.1:5004",
                    first_contact=datetime.now(UTC),
                    lost_at=None,
                    version="24.03.0",
                    architecture="x86_64",
                    compute_plugins={},
                    schedulable=False,
                )
            )
            await sess.flush()
        return AgentFixtureData(
            id=agent_id, scaling_group=scaling_group.name, available_slots=available_slots
        )

    @pytest.fixture
    async def agent_in_sg2(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
        scaling_group2: ScalingGroupFixtureData,
    ) -> AgentFixtureData:
        """Create an agent in scaling_group2."""
        agent_id = f"agent-sg2-{uuid.uuid4().hex[:8]}"
        available_slots: dict[str, Decimal] = {"cpu": Decimal("16")}
        async with db_with_tables.begin_session() as sess:
            sess.add(
                AgentRow(
                    id=AgentId(agent_id),
                    status=AgentStatus.ALIVE,
                    region="local",
                    scaling_group=scaling_group2.name,
                    available_slots=ResourceSlot(available_slots),
                    occupied_slots=ResourceSlot({}),
                    addr="tcp://127.0.0.1:5005",
                    first_contact=datetime.now(UTC),
                    lost_at=None,
                    version="24.03.0",
                    architecture="x86_64",
                    compute_plugins={},
                    schedulable=True,
                )
            )
            await sess.flush()
        return AgentFixtureData(
            id=agent_id, scaling_group=scaling_group2.name, available_slots=available_slots
        )

    @pytest.fixture
    def db_source(self, db_with_tables: ExtendedAsyncSAEngine) -> ScheduleDBSource:
        """Create ScheduleDBSource instance."""
        return ScheduleDBSource(db_with_tables)

    @pytest.mark.asyncio
    async def test_returns_aggregated_slots_for_scaling_group(
        self,
        db_source: ScheduleDBSource,
        scaling_group: ScalingGroupFixtureData,
        agent: AgentFixtureData,
        agent2: AgentFixtureData,
    ) -> None:
        """Test that resources are correctly aggregated for agents in a scaling group."""
        result = await db_source.calculate_total_resource_slots_by_scaling_group(scaling_group.name)

        expected_cpu = agent.available_slots["cpu"] + agent2.available_slots["cpu"]
        expected_mem = agent.available_slots["mem"] + agent2.available_slots["mem"]

        assert result.total_capacity_slots["cpu"] == expected_cpu
        assert result.total_capacity_slots["mem"] == expected_mem
        assert result.total_used_slots.get("cpu", Decimal("0")) == Decimal("0")
        assert result.total_free_slots["cpu"] == expected_cpu

    @pytest.mark.asyncio
    async def test_returns_empty_slots_for_nonexistent_scaling_group(
        self,
        db_source: ScheduleDBSource,
    ) -> None:
        """Test that empty slots are returned for non-existent scaling group."""
        result = await db_source.calculate_total_resource_slots_by_scaling_group("nonexistent-sg")

        assert len(result.total_capacity_slots) == 0
        assert len(result.total_used_slots) == 0
        assert len(result.total_free_slots) == 0

    @pytest.mark.asyncio
    async def test_excludes_terminated_agent(
        self,
        db_source: ScheduleDBSource,
        scaling_group: ScalingGroupFixtureData,
        agent: AgentFixtureData,
        terminated_agent: AgentFixtureData,
    ) -> None:
        """Test that TERMINATED agents are excluded from calculation."""
        result = await db_source.calculate_total_resource_slots_by_scaling_group(scaling_group.name)

        assert result.total_capacity_slots["cpu"] == agent.available_slots["cpu"]

    @pytest.mark.asyncio
    async def test_excludes_non_schedulable_agent(
        self,
        db_source: ScheduleDBSource,
        scaling_group: ScalingGroupFixtureData,
        agent: AgentFixtureData,
        non_schedulable_agent: AgentFixtureData,
    ) -> None:
        """Test that non-schedulable agents are excluded from calculation."""
        result = await db_source.calculate_total_resource_slots_by_scaling_group(scaling_group.name)

        assert result.total_capacity_slots["cpu"] == agent.available_slots["cpu"]

    @pytest.mark.asyncio
    async def test_only_counts_agents_in_specified_scaling_group(
        self,
        db_source: ScheduleDBSource,
        scaling_group: ScalingGroupFixtureData,
        scaling_group2: ScalingGroupFixtureData,
        agent: AgentFixtureData,
        agent_in_sg2: AgentFixtureData,
    ) -> None:
        """Test that only agents in the specified scaling group are counted."""
        result_sg1 = await db_source.calculate_total_resource_slots_by_scaling_group(
            scaling_group.name
        )
        result_sg2 = await db_source.calculate_total_resource_slots_by_scaling_group(
            scaling_group2.name
        )

        assert result_sg1.total_capacity_slots["cpu"] == agent.available_slots["cpu"]
        assert result_sg2.total_capacity_slots["cpu"] == agent_in_sg2.available_slots["cpu"]

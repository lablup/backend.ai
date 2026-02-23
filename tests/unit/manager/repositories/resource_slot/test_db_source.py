"""Integration tests for ResourceSlotDBSource with real database."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from dateutil.tz import tzutc

from ai.backend.common.types import ResourceSlot, SlotName
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.errors.resource_slot import (
    ResourceSlotTypeNotFound,
)
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_policy import ProjectResourcePolicyRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.scaling_group import ScalingGroupOpts, ScalingGroupRow
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.base.pagination import OffsetPagination
from ai.backend.manager.repositories.resource_slot.db_source import ResourceSlotDBSource
from ai.backend.testutils.db import with_tables


class TestSlotTypes:
    """Tests for resource_slot_types read operations."""

    async def test_all_slot_types(
        self,
        db_source: ResourceSlotDBSource,
        slot_types: list[str],
    ) -> None:
        types = await db_source.all_slot_types()
        assert len(types) == 2
        names = [t.slot_name for t in types]
        assert "cpu" in names
        assert "mem" in names

    async def test_get_slot_type_found(
        self,
        db_source: ResourceSlotDBSource,
        slot_types: list[str],
    ) -> None:
        slot_type = await db_source.get_slot_type("cpu")
        assert slot_type.slot_name == "cpu"
        assert slot_type.slot_type == "count"

    async def test_get_slot_type_not_found(
        self,
        db_source: ResourceSlotDBSource,
        slot_types: list[str],
    ) -> None:
        with pytest.raises(ResourceSlotTypeNotFound):
            await db_source.get_slot_type("nonexistent")


class TestAgentResources:
    """Tests for agent_resources read operations."""

    @pytest.fixture
    async def db_with_agent_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [ScalingGroupRow, AgentRow, ResourceSlotTypeRow, AgentResourceRow],
        ):
            async with database_connection.begin_session() as db_sess:
                for name, stype in [("cpu", "count"), ("mem", "bytes")]:
                    db_sess.add(ResourceSlotTypeRow(slot_name=name, slot_type=stype, rank=0))
            yield database_connection

    async def _seed_agent(
        self, db: ExtendedAsyncSAEngine
    ) -> tuple[str, Decimal, Decimal, Decimal, Decimal]:
        cpu_capacity = Decimal("8")
        cpu_used = Decimal("2")
        mem_capacity = Decimal("32768")
        mem_used = Decimal("4096")
        sg_name = str(uuid4())
        agent_id = str(uuid4())
        async with db.begin_session() as db_sess:
            db_sess.add(
                ScalingGroupRow(
                    name=sg_name,
                    driver="static",
                    driver_opts={},
                    scheduler="fifo",
                    scheduler_opts=ScalingGroupOpts(),
                )
            )
        async with db.begin_session() as db_sess:
            db_sess.add(
                AgentRow(
                    id=agent_id,
                    status=AgentStatus.ALIVE,
                    status_changed=datetime.now(tzutc()),
                    region="test-region",
                    scaling_group=sg_name,
                    available_slots=ResourceSlot({SlotName("cpu"): "8"}),
                    occupied_slots=ResourceSlot({}),
                    addr="tcp://127.0.0.1:6001",
                    version="24.12.0",
                    architecture="x86_64",
                    compute_plugins={},
                )
            )
        async with db.begin_session() as db_sess:
            db_sess.add(
                AgentResourceRow(
                    agent_id=agent_id,
                    slot_name="cpu",
                    capacity=cpu_capacity,
                    used=cpu_used,
                )
            )
            db_sess.add(
                AgentResourceRow(
                    agent_id=agent_id,
                    slot_name="mem",
                    capacity=mem_capacity,
                    used=mem_used,
                )
            )
        return agent_id, cpu_capacity, cpu_used, mem_capacity, mem_used

    async def test_get_agent_resources(
        self,
        db_with_agent_tables: ExtendedAsyncSAEngine,
    ) -> None:
        agent_id, cpu_capacity, cpu_used, mem_capacity, _ = await self._seed_agent(
            db_with_agent_tables
        )
        db_source = ResourceSlotDBSource(db_with_agent_tables)

        rows = await db_source.get_agent_resources(agent_id)

        assert len(rows) == 2
        by_slot = {r.slot_name: r for r in rows}
        assert by_slot["cpu"].capacity == cpu_capacity
        assert by_slot["cpu"].used == cpu_used
        assert by_slot["mem"].capacity == mem_capacity

    async def test_get_agent_resources_empty(
        self,
        db_with_agent_tables: ExtendedAsyncSAEngine,
    ) -> None:
        db_source = ResourceSlotDBSource(db_with_agent_tables)
        rows = await db_source.get_agent_resources("nonexistent-agent")
        assert rows == []

    async def test_search_agent_resources(
        self,
        db_with_agent_tables: ExtendedAsyncSAEngine,
    ) -> None:
        agent_id, cpu_capacity, cpu_used, _, _ = await self._seed_agent(db_with_agent_tables)
        db_source = ResourceSlotDBSource(db_with_agent_tables)
        querier = BatchQuerier(pagination=OffsetPagination(offset=0, limit=10))

        result = await db_source.search_agent_resources(querier)

        expected_count = 2
        assert result.total_count == expected_count
        assert len(result.items) == expected_count
        assert not result.has_next_page
        cpu_item = next(item for item in result.items if item.slot_name == "cpu")
        assert cpu_item.agent_id == agent_id
        assert cpu_item.capacity == cpu_capacity
        assert cpu_item.used == cpu_used

    async def test_search_agent_resources_empty(
        self,
        db_with_agent_tables: ExtendedAsyncSAEngine,
    ) -> None:
        db_source = ResourceSlotDBSource(db_with_agent_tables)
        querier = BatchQuerier(pagination=OffsetPagination(offset=0, limit=10))

        result = await db_source.search_agent_resources(querier)

        assert result.total_count == 0
        assert result.items == []


class TestResourceAllocations:
    """Tests for resource_allocations read operations."""

    @pytest.fixture
    async def db_with_allocation_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        # Full FK chain: DomainRow, ProjectResourcePolicyRow, ScalingGroupRow, GroupRow,
        # AgentRow, SessionRow, KernelRow, ResourceSlotTypeRow → ResourceAllocationRow
        async with with_tables(
            database_connection,
            [
                DomainRow,
                ProjectResourcePolicyRow,
                ScalingGroupRow,
                GroupRow,
                AgentRow,
                SessionRow,
                KernelRow,
                ResourceSlotTypeRow,
                ResourceAllocationRow,
            ],
        ):
            yield database_connection

    async def test_get_kernel_allocations_empty(
        self,
        db_with_allocation_tables: ExtendedAsyncSAEngine,
    ) -> None:
        db_source = ResourceSlotDBSource(db_with_allocation_tables)
        rows = await db_source.get_kernel_allocations(uuid4())
        assert rows == []

    async def test_search_resource_allocations_empty(
        self,
        db_with_allocation_tables: ExtendedAsyncSAEngine,
    ) -> None:
        db_source = ResourceSlotDBSource(db_with_allocation_tables)
        querier = BatchQuerier(pagination=OffsetPagination(offset=0, limit=10))
        result = await db_source.search_resource_allocations(querier)
        assert result.total_count == 0
        assert result.items == []

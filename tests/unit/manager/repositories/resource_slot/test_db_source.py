"""Integration tests for ResourceSlotDBSource with real database."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
import sqlalchemy as sa

from ai.backend.common.types import AgentId, SlotQuantity
from ai.backend.manager.errors.resource_slot import (
    AgentResourceCapacityExceeded,
    ResourceSlotTypeNotFound,
)
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import (
    BulkUpserter,
)
from ai.backend.manager.repositories.resource_slot.db_source import ResourceSlotDBSource
from ai.backend.manager.repositories.resource_slot.upserters import AgentResourceUpserterSpec


class TestRequestResources:
    """Tests for request_resources (INSERT only, no agent involvement)."""

    async def test_request_resources(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        db_source: ResourceSlotDBSource,
        kernel_id: uuid.UUID,
        slot_types: list[str],
    ) -> None:
        """Should INSERT allocation rows with requested amounts only."""
        count = await db_source.request_resources(
            kernel_id,
            [
                SlotQuantity(slot_name="cpu", quantity=Decimal("2")),
                SlotQuantity(slot_name="mem", quantity=Decimal("4294967296")),
            ],
        )
        assert count == 2

        async with (
            database_with_resource_slot_tables.begin_readonly_session_read_committed() as db_sess
        ):
            result = await db_sess.execute(
                sa.select(ResourceAllocationRow).where(
                    ResourceAllocationRow.kernel_id == kernel_id,
                )
            )
            rows = result.scalars().all()
            assert len(rows) == 2
            by_name = {r.slot_name: r for r in rows}
            assert by_name["cpu"].requested == Decimal("2")
            assert by_name["cpu"].used is None
            assert by_name["cpu"].free_at is None

    async def test_request_resources_empty(
        self,
        db_source: ResourceSlotDBSource,
        kernel_id: uuid.UUID,
        slot_types: list[str],
    ) -> None:
        count = await db_source.request_resources(kernel_id, [])
        assert count == 0


class TestAllocateResources:
    """Tests for allocate_resources (set used + increment agent)."""

    async def test_allocate_resources(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        db_source: ResourceSlotDBSource,
        kernel_id: uuid.UUID,
        agent_with_capacity: str,
    ) -> None:
        """Should set used on allocations and increment agent_resources.used."""
        await db_source.request_resources(
            kernel_id,
            [
                SlotQuantity(slot_name="cpu", quantity=Decimal("4")),
                SlotQuantity(slot_name="mem", quantity=Decimal("4294967296")),
            ],
        )
        count = await db_source.allocate_resources(
            kernel_id,
            agent_with_capacity,
            [
                SlotQuantity(slot_name="cpu", quantity=Decimal("2")),
                SlotQuantity(slot_name="mem", quantity=Decimal("2147483648")),
            ],
        )
        assert count == 2

        async with (
            database_with_resource_slot_tables.begin_readonly_session_read_committed() as db_sess
        ):
            alloc_result = await db_sess.execute(
                sa.select(ResourceAllocationRow).where(
                    ResourceAllocationRow.kernel_id == kernel_id,
                )
            )
            by_name = {r.slot_name: r for r in alloc_result.scalars().all()}
            assert by_name["cpu"].used == Decimal("2")
            assert by_name["cpu"].used_at is not None

            agent_result = await db_sess.execute(
                sa.select(AgentResourceRow).where(
                    AgentResourceRow.agent_id == agent_with_capacity,
                )
            )
            agent_rows = {r.slot_name: r for r in agent_result.scalars().all()}
            assert agent_rows["cpu"].used == Decimal("2")
            assert agent_rows["mem"].used == Decimal("2147483648")

    async def test_allocate_resources_capacity_exceeded(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        db_source: ResourceSlotDBSource,
        kernel_id: uuid.UUID,
        agent_with_capacity: str,
    ) -> None:
        """Exceeding capacity should rollback the transaction."""
        await db_source.request_resources(
            kernel_id,
            [SlotQuantity(slot_name="cpu", quantity=Decimal("100"))],
        )
        with pytest.raises(AgentResourceCapacityExceeded):
            await db_source.allocate_resources(
                kernel_id,
                agent_with_capacity,
                [SlotQuantity(slot_name="cpu", quantity=Decimal("100"))],
            )

        async with (
            database_with_resource_slot_tables.begin_readonly_session_read_committed() as db_sess
        ):
            agent_result = await db_sess.execute(
                sa.select(AgentResourceRow).where(
                    AgentResourceRow.agent_id == agent_with_capacity,
                )
            )
            for row in agent_result.scalars().all():
                assert row.used == Decimal("0")

    async def test_allocate_resources_empty(
        self,
        db_source: ResourceSlotDBSource,
        kernel_id: uuid.UUID,
        agent_with_capacity: str,
    ) -> None:
        count = await db_source.allocate_resources(kernel_id, agent_with_capacity, [])
        assert count == 0


class TestFreeResources:
    """Tests for free_resources (set free_at + decrement agent)."""

    async def test_free_resources(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        db_source: ResourceSlotDBSource,
        kernel_id: uuid.UUID,
        agent_with_capacity: str,
    ) -> None:
        """Should set free_at and decrement agent_resources.used."""
        await db_source.request_resources(
            kernel_id,
            [
                SlotQuantity(slot_name="cpu", quantity=Decimal("4")),
                SlotQuantity(slot_name="mem", quantity=Decimal("4294967296")),
            ],
        )
        await db_source.allocate_resources(
            kernel_id,
            agent_with_capacity,
            [
                SlotQuantity(slot_name="cpu", quantity=Decimal("2")),
                SlotQuantity(slot_name="mem", quantity=Decimal("2147483648")),
            ],
        )
        freed = await db_source.free_resources(kernel_id, agent_with_capacity)
        assert freed == 2

        async with (
            database_with_resource_slot_tables.begin_readonly_session_read_committed() as db_sess
        ):
            alloc_result = await db_sess.execute(
                sa.select(ResourceAllocationRow).where(
                    ResourceAllocationRow.kernel_id == kernel_id,
                )
            )
            for row in alloc_result.scalars().all():
                assert row.free_at is not None

            agent_result = await db_sess.execute(
                sa.select(AgentResourceRow).where(
                    AgentResourceRow.agent_id == agent_with_capacity,
                )
            )
            for row in agent_result.scalars().all():
                assert row.used == Decimal("0")

    async def test_free_resources_idempotent(
        self,
        db_source: ResourceSlotDBSource,
        kernel_id: uuid.UUID,
        agent_with_capacity: str,
    ) -> None:
        """Freeing already-freed allocations should return 0."""
        await db_source.request_resources(
            kernel_id,
            [SlotQuantity(slot_name="cpu", quantity=Decimal("4"))],
        )
        await db_source.allocate_resources(
            kernel_id,
            agent_with_capacity,
            [SlotQuantity(slot_name="cpu", quantity=Decimal("1"))],
        )
        await db_source.free_resources(kernel_id, agent_with_capacity)

        freed = await db_source.free_resources(kernel_id, agent_with_capacity)
        assert freed == 0


class TestAgentResourcesCRUD:
    """Tests for agent_resources UPSERT operations."""

    async def test_upsert_agent_capacity_insert(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        db_source: ResourceSlotDBSource,
        agent_id: str,
        slot_types: list[str],
    ) -> None:
        bulk_upserter: BulkUpserter[AgentResourceRow] = BulkUpserter(
            specs=[
                AgentResourceUpserterSpec(
                    agent_id=agent_id, slot_name="cpu", capacity=Decimal("8")
                ),
                AgentResourceUpserterSpec(
                    agent_id=agent_id, slot_name="mem", capacity=Decimal("8589934592")
                ),
            ],
        )

        count = await db_source.upsert_agent_capacity(bulk_upserter)
        assert count == 2

        async with (
            database_with_resource_slot_tables.begin_readonly_session_read_committed() as db_sess
        ):
            result = await db_sess.execute(
                sa.select(AgentResourceRow).where(
                    AgentResourceRow.agent_id == agent_id,
                )
            )
            rows = result.scalars().all()
            assert len(rows) == 2
            by_name = {r.slot_name: r for r in rows}
            assert by_name["cpu"].capacity == Decimal("8")
            assert by_name["cpu"].used == Decimal("0")

    async def test_upsert_agent_capacity_update(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        db_source: ResourceSlotDBSource,
        agent_with_capacity: str,
    ) -> None:
        bulk_upserter: BulkUpserter[AgentResourceRow] = BulkUpserter(
            specs=[
                AgentResourceUpserterSpec(
                    agent_id=agent_with_capacity, slot_name="cpu", capacity=Decimal("16")
                ),
                AgentResourceUpserterSpec(
                    agent_id=agent_with_capacity, slot_name="mem", capacity=Decimal("17179869184")
                ),
            ],
        )
        await db_source.upsert_agent_capacity(bulk_upserter)

        async with (
            database_with_resource_slot_tables.begin_readonly_session_read_committed() as db_sess
        ):
            result = await db_sess.execute(
                sa.select(AgentResourceRow).where(
                    AgentResourceRow.agent_id == agent_with_capacity,
                )
            )
            rows = result.scalars().all()
            by_name = {r.slot_name: r for r in rows}
            assert by_name["cpu"].capacity == Decimal("16")
            assert by_name["mem"].capacity == Decimal("17179869184")

    async def test_upsert_empty_slots(
        self,
        db_source: ResourceSlotDBSource,
        agent_id: str,
        slot_types: list[str],
    ) -> None:
        bulk_upserter: BulkUpserter[AgentResourceRow] = BulkUpserter(
            specs=[],
        )
        count = await db_source.upsert_agent_capacity(bulk_upserter)
        assert count == 0


class TestGetAgentOccupancy:
    """Tests for get_agent_occupancy (reads agent_resources.used)."""

    async def test_get_agent_occupancy_with_used(
        self,
        db_source: ResourceSlotDBSource,
        kernel_id: uuid.UUID,
        agent_with_capacity: str,
    ) -> None:
        """Should return used values from agent_resources."""
        await db_source.request_resources(
            kernel_id,
            [
                SlotQuantity(slot_name="cpu", quantity=Decimal("4")),
                SlotQuantity(slot_name="mem", quantity=Decimal("4294967296")),
            ],
        )
        await db_source.allocate_resources(
            kernel_id,
            agent_with_capacity,
            [
                SlotQuantity(slot_name="cpu", quantity=Decimal("2")),
                SlotQuantity(slot_name="mem", quantity=Decimal("2147483648")),
            ],
        )

        aid = AgentId(agent_with_capacity)
        results = await db_source.get_agent_occupancy({aid})
        assert len(results) == 1
        assert results[0].agent_id == aid
        by_name = {s.slot_name: s.quantity for s in results[0].slots}
        assert by_name["cpu"] == Decimal("2")
        assert by_name["mem"] == Decimal("2147483648")

    async def test_get_agent_occupancy_empty_input(
        self,
        db_source: ResourceSlotDBSource,
        slot_types: list[str],
    ) -> None:
        results = await db_source.get_agent_occupancy(set())
        assert results == []

    async def test_get_agent_occupancy_no_used(
        self,
        db_source: ResourceSlotDBSource,
        agent_with_capacity: str,
    ) -> None:
        """Agent with used=0 should still return all slots."""
        aid = AgentId(agent_with_capacity)
        results = await db_source.get_agent_occupancy({aid})
        assert len(results) == 1
        assert results[0].agent_id == aid
        assert len(results[0].slots) == 2
        by_name = {s.slot_name: s.quantity for s in results[0].slots}
        assert by_name["cpu"] == Decimal("0")
        assert by_name["mem"] == Decimal("0")


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

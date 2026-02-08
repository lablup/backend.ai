"""Tests for resource slot normalization tables.

Verifies CRUD operations, constraints, and data integrity for:
- resource_slot_types
- agent_resources
- resource_allocations
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
import sqlalchemy as sa

from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class TestResourceSlotTypeRow:
    """Tests for resource_slot_types table."""

    async def test_insert_and_select(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
    ) -> None:
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                ResourceSlotTypeRow(
                    slot_name="cpu",
                    slot_type="count",
                    display_name="CPU",
                    rank=40,
                )
            )
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(ResourceSlotTypeRow, "cpu")
            assert row is not None
            assert row.slot_name == "cpu"
            assert row.slot_type == "count"
            assert row.display_name == "CPU"
            assert row.rank == 40
            assert row.created_at is not None
            assert row.updated_at is not None

    async def test_duplicate_slot_name_raises(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
    ) -> None:
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
            await db_sess.flush()

        with pytest.raises(sa.exc.IntegrityError):
            async with database_with_resource_slot_tables.begin_session() as db_sess:
                db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="bytes"))
                await db_sess.flush()

    async def test_nullable_display_fields(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
    ) -> None:
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                ResourceSlotTypeRow(
                    slot_name="custom.device",
                    slot_type="count",
                )
            )
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(ResourceSlotTypeRow, "custom.device")
            assert row is not None
            assert row.display_name is None

    async def test_server_defaults(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
    ) -> None:
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="test.slot", slot_type="count"))
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(ResourceSlotTypeRow, "test.slot")
            assert row is not None
            assert row.rank == 0


class TestAgentResourceRow:
    """Tests for agent_resources table."""

    async def test_insert_and_select(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        agent_id: str,
    ) -> None:
        # Seed slot type
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                AgentResourceRow(
                    agent_id=agent_id,
                    slot_name="cpu",
                    capacity=Decimal("4.000000"),
                    used=Decimal("1.500000"),
                )
            )
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(AgentResourceRow, (agent_id, "cpu"))
            assert row is not None
            assert row.capacity == Decimal("4.000000")
            assert row.used == Decimal("1.500000")

    async def test_composite_pk(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        agent_id: str,
    ) -> None:
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
            db_sess.add(ResourceSlotTypeRow(slot_name="mem", slot_type="bytes"))
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                AgentResourceRow(
                    agent_id=agent_id,
                    slot_name="cpu",
                    capacity=Decimal("4"),
                )
            )
            db_sess.add(
                AgentResourceRow(
                    agent_id=agent_id,
                    slot_name="mem",
                    capacity=Decimal("4294967296"),
                )
            )
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            stmt = sa.select(AgentResourceRow).where(AgentResourceRow.agent_id == agent_id)
            result = await db_sess.execute(stmt)
            rows = result.scalars().all()
            assert len(rows) == 2
            slot_names = {r.slot_name for r in rows}
            assert slot_names == {"cpu", "mem"}

    async def test_cascade_delete_on_agent(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        agent_id: str,
    ) -> None:
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                AgentResourceRow(
                    agent_id=agent_id,
                    slot_name="cpu",
                    capacity=Decimal("4"),
                )
            )
            await db_sess.flush()

        # Delete agent via raw SQL to trigger CASCADE
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            await db_sess.execute(
                sa.text("DELETE FROM agents WHERE id = :aid"),
                {"aid": agent_id},
            )

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(AgentResourceRow, (agent_id, "cpu"))
            assert row is None

    async def test_numeric_precision_large_memory(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        agent_id: str,
    ) -> None:
        """Verify NUMERIC(24,6) handles large byte values (e.g., 1 TiB)."""
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="mem", slot_type="bytes"))
            await db_sess.flush()

        one_tib = Decimal("1099511627776.000000")  # 1 TiB in bytes
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                AgentResourceRow(
                    agent_id=agent_id,
                    slot_name="mem",
                    capacity=one_tib,
                )
            )
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(AgentResourceRow, (agent_id, "mem"))
            assert row is not None
            assert row.capacity == one_tib

    async def test_numeric_precision_fractional_cpu(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        agent_id: str,
    ) -> None:
        """Verify NUMERIC(24,6) handles fractional values (e.g., 0.5 CPU)."""
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
            await db_sess.flush()

        half_cpu = Decimal("0.500000")
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                AgentResourceRow(
                    agent_id=agent_id,
                    slot_name="cpu",
                    capacity=half_cpu,
                )
            )
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(AgentResourceRow, (agent_id, "cpu"))
            assert row is not None
            assert row.capacity == half_cpu

    async def test_used_nullable(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        agent_id: str,
    ) -> None:
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                AgentResourceRow(
                    agent_id=agent_id,
                    slot_name="cpu",
                    capacity=Decimal("4"),
                    used=None,
                )
            )
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(AgentResourceRow, (agent_id, "cpu"))
            assert row is not None
            assert row.used is None

    async def test_fk_constraint_on_slot_name(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        agent_id: str,
    ) -> None:
        """FK to resource_slot_types should reject unknown slot names."""
        with pytest.raises(sa.exc.IntegrityError):
            async with database_with_resource_slot_tables.begin_session() as db_sess:
                db_sess.add(
                    AgentResourceRow(
                        agent_id=agent_id,
                        slot_name="nonexistent.slot",
                        capacity=Decimal("1"),
                    )
                )
                await db_sess.flush()


class TestResourceAllocationRow:
    """Tests for resource_allocations table."""

    async def test_insert_and_select(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        kernel_id: uuid.UUID,
    ) -> None:
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="cpu",
                    requested=Decimal("2.000000"),
                    used=Decimal("1.500000"),
                )
            )
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(ResourceAllocationRow, (kernel_id, "cpu"))
            assert row is not None
            assert row.requested == Decimal("2.000000")
            assert row.used == Decimal("1.500000")

    async def test_composite_pk(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        kernel_id: uuid.UUID,
    ) -> None:
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
            db_sess.add(ResourceSlotTypeRow(slot_name="mem", slot_type="bytes"))
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="cpu",
                    requested=Decimal("1"),
                )
            )
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="mem",
                    requested=Decimal("1073741824"),
                )
            )
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            stmt = sa.select(ResourceAllocationRow).where(
                ResourceAllocationRow.kernel_id == kernel_id
            )
            result = await db_sess.execute(stmt)
            rows = result.scalars().all()
            assert len(rows) == 2

    async def test_cascade_delete_on_kernel(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        kernel_id: uuid.UUID,
    ) -> None:
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="cpu",
                    requested=Decimal("1"),
                )
            )
            await db_sess.flush()

        # Delete kernel via raw SQL to trigger CASCADE
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            await db_sess.execute(
                sa.text("DELETE FROM kernels WHERE id = :kid"),
                {"kid": str(kernel_id)},
            )

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(ResourceAllocationRow, (kernel_id, "cpu"))
            assert row is None

    async def test_used_nullable(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        kernel_id: uuid.UUID,
    ) -> None:
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="cpu",
                    requested=Decimal("1"),
                    used=None,
                )
            )
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(ResourceAllocationRow, (kernel_id, "cpu"))
            assert row is not None
            assert row.used is None
            assert row.used_at is None

    async def test_fk_constraint_on_slot_name(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        kernel_id: uuid.UUID,
    ) -> None:
        """FK to resource_slot_types should reject unknown slot names."""
        with pytest.raises(sa.exc.IntegrityError):
            async with database_with_resource_slot_tables.begin_session() as db_sess:
                db_sess.add(
                    ResourceAllocationRow(
                        kernel_id=kernel_id,
                        slot_name="nonexistent.slot",
                        requested=Decimal("1"),
                    )
                )
                await db_sess.flush()

    async def test_fk_constraint_on_kernel_id(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """FK to kernels should reject non-existent kernel IDs."""
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="cpu", slot_type="count"))
            await db_sess.flush()

        with pytest.raises(sa.exc.IntegrityError):
            async with database_with_resource_slot_tables.begin_session() as db_sess:
                db_sess.add(
                    ResourceAllocationRow(
                        kernel_id=uuid.uuid4(),
                        slot_name="cpu",
                        requested=Decimal("1"),
                    )
                )
                await db_sess.flush()

    async def test_numeric_precision_large_memory_allocation(
        self,
        database_with_resource_slot_tables: ExtendedAsyncSAEngine,
        kernel_id: uuid.UUID,
    ) -> None:
        """Verify NUMERIC(24,6) handles large byte values for memory allocation."""
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(ResourceSlotTypeRow(slot_name="mem", slot_type="bytes"))
            await db_sess.flush()

        one_tib = Decimal("1099511627776.000000")
        async with database_with_resource_slot_tables.begin_session() as db_sess:
            db_sess.add(
                ResourceAllocationRow(
                    kernel_id=kernel_id,
                    slot_name="mem",
                    requested=one_tib,
                    used=one_tib,
                )
            )
            await db_sess.flush()

        async with database_with_resource_slot_tables.begin_session() as db_sess:
            row = await db_sess.get(ResourceAllocationRow, (kernel_id, "mem"))
            assert row is not None
            assert row.requested == one_tib
            assert row.used == one_tib

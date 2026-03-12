"""Database source for Resource Slot repository operations."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.common.types import SlotQuantity
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    AgentResourceDrift,
    AgentResourceSearchResult,
    NumberFormatData,
    ResourceAllocationData,
    ResourceAllocationSearchResult,
    ResourceOccupancy,
    ResourceSlotTypeData,
    ResourceSlotTypeSearchResult,
)
from ai.backend.manager.errors.resource_slot import (
    ResourceSlotTypeNotFound,
)
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.repositories.base import (
    BatchQuerier,
    execute_batch_querier,
)

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

__all__ = ("ResourceSlotDBSource",)


class ResourceSlotDBSource:
    """Database source for Resource Slot operations.

    Manages three normalized tables:
    - resource_slot_types: Registry of known slot types
    - agent_resources: Per-agent, per-slot capacity and usage
    - resource_allocations: Per-kernel, per-slot resource allocation
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db

    # ==================== resource_slot_types Read ====================

    async def all_slot_types(self) -> list[ResourceSlotTypeRow]:
        """List all registered resource slot types.

        Returns:
            List of ResourceSlotTypeRow ordered by rank, then slot_name.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            stmt = sa.select(ResourceSlotTypeRow).order_by(
                ResourceSlotTypeRow.rank,
                ResourceSlotTypeRow.slot_name,
            )
            result = await db_sess.execute(stmt)
            return list(result.scalars().all())

    async def get_slot_type(
        self,
        slot_name: str,
    ) -> ResourceSlotTypeRow:
        """Get a specific resource slot type by name.

        Args:
            slot_name: The slot type name to look up.

        Returns:
            ResourceSlotTypeRow for the given slot name.

        Raises:
            ResourceSlotTypeNotFound: If the slot type does not exist.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            stmt = sa.select(ResourceSlotTypeRow).where(
                ResourceSlotTypeRow.slot_name == slot_name,
            )
            result = await db_sess.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                raise ResourceSlotTypeNotFound(f"Resource slot type '{slot_name}' not found.")
            return row

    async def search_slot_types(self, querier: BatchQuerier) -> ResourceSlotTypeSearchResult:
        """Paginated search across all resource_slot_types rows."""
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(ResourceSlotTypeRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [
                ResourceSlotTypeData(
                    slot_name=row.ResourceSlotTypeRow.slot_name,
                    slot_type=row.ResourceSlotTypeRow.slot_type,
                    display_name=row.ResourceSlotTypeRow.display_name,
                    description=row.ResourceSlotTypeRow.description,
                    display_unit=row.ResourceSlotTypeRow.display_unit,
                    display_icon=row.ResourceSlotTypeRow.display_icon,
                    number_format=NumberFormatData(
                        binary=row.ResourceSlotTypeRow.number_format.binary,
                        round_length=row.ResourceSlotTypeRow.number_format.round_length,
                    ),
                    rank=row.ResourceSlotTypeRow.rank,
                )
                for row in result.rows
            ]
            return ResourceSlotTypeSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ==================== agent_resources Read ====================

    async def get_agent_resources(self, agent_id: str) -> list[AgentResourceRow]:
        # Returns all slot capacity/usage rows for one agent, ordered by slot_name for consistency.
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            stmt = (
                sa.select(AgentResourceRow)
                .where(AgentResourceRow.agent_id == agent_id)
                .order_by(AgentResourceRow.slot_name)
            )
            result = await db_sess.execute(stmt)
            return list(result.scalars().all())

    async def search_agent_resources(self, querier: BatchQuerier) -> AgentResourceSearchResult:
        # Paginated search across all agent_resources rows.
        # Caller injects conditions (e.g. by_slot_name, by_agent_id) via querier.
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(AgentResourceRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [
                AgentResourceData(
                    agent_id=row.AgentResourceRow.agent_id,
                    slot_name=row.AgentResourceRow.slot_name,
                    capacity=row.AgentResourceRow.capacity,
                    used=row.AgentResourceRow.used,
                )
                for row in result.rows
            ]
            return AgentResourceSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ==================== resource_allocations Read ====================

    async def get_kernel_allocations(self, kernel_id: uuid.UUID) -> list[ResourceAllocationRow]:
        # Returns all per-slot requested/used allocation rows for one kernel (container).
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            stmt = (
                sa.select(ResourceAllocationRow)
                .where(ResourceAllocationRow.kernel_id == kernel_id)
                .order_by(ResourceAllocationRow.slot_name)
            )
            result = await db_sess.execute(stmt)
            return list(result.scalars().all())

    async def search_resource_allocations(
        self, querier: BatchQuerier
    ) -> ResourceAllocationSearchResult:
        # Paginated search across all resource_allocations rows.
        # Caller injects conditions (e.g. by_slot_name, by_kernel_id) via querier.
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            query = sa.select(ResourceAllocationRow)
            result = await execute_batch_querier(db_sess, query, querier)
            items = [
                ResourceAllocationData(
                    kernel_id=row.ResourceAllocationRow.kernel_id,
                    slot_name=row.ResourceAllocationRow.slot_name,
                    requested=row.ResourceAllocationRow.requested,
                    used=row.ResourceAllocationRow.used,
                )
                for row in result.rows
            ]
            return ResourceAllocationSearchResult(
                items=items,
                total_count=result.total_count,
                has_next_page=result.has_next_page,
                has_previous_page=result.has_previous_page,
            )

    # ==================== Aggregation Queries ====================

    async def aggregate_occupied_by_domain(self, domain_name: str) -> ResourceOccupancy:
        """Aggregate active resource occupancy for a domain.

        Joins resource_allocations → kernels → resource_slot_types.
        Only includes kernels with resource-occupying/requesting statuses and free_at IS NULL.

        Returns:
            ResourceOccupancy with used_slots (sorted by rank) and session_count.
        """
        ra = ResourceAllocationRow.__table__
        k = KernelRow.__table__
        rst = ResourceSlotTypeRow.__table__
        all_resource_statuses = (
            KernelStatus.resource_occupied_statuses() | KernelStatus.resource_requested_statuses()
        )
        effective_amount = sa.func.coalesce(ra.c.used, ra.c.requested)
        common_where = (
            k.c.domain_name == domain_name,
            k.c.status.in_(all_resource_statuses),
            ra.c.free_at.is_(None),
        )
        slot_stmt = (
            sa.select(
                ra.c.slot_name,
                sa.func.sum(effective_amount).label("total_amount"),
                rst.c.rank,
            )
            .select_from(
                ra.join(k, ra.c.kernel_id == k.c.id).join(rst, ra.c.slot_name == rst.c.slot_name)
            )
            .where(*common_where)
            .group_by(ra.c.slot_name, rst.c.rank)
        )
        count_stmt = (
            sa.select(sa.func.count(sa.distinct(k.c.session_id)).label("session_count"))
            .select_from(ra.join(k, ra.c.kernel_id == k.c.id))
            .where(*common_where)
        )
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            slot_rows = (await db_sess.execute(slot_stmt)).all()
            (session_count,) = (await db_sess.execute(count_stmt)).one()

        rank_map = {row.slot_name: row.rank for row in slot_rows}
        used_slots = sorted(
            [SlotQuantity(slot_name=row.slot_name, quantity=row.total_amount) for row in slot_rows],
            key=lambda sq: rank_map.get(sq.slot_name, 9999),
        )
        return ResourceOccupancy(used_slots=used_slots, session_count=session_count)

    def _build_actual_usage_query(self) -> sa.Select[tuple[str, str, Decimal]]:
        """Build the query to compute actual per-agent per-slot resource usage."""
        ra = ResourceAllocationRow.__table__
        k = KernelRow.__table__
        all_resource_statuses = (
            KernelStatus.resource_occupied_statuses() | KernelStatus.resource_requested_statuses()
        )
        effective_amount = sa.func.coalesce(ra.c.used, ra.c.requested)
        return (
            sa.select(
                k.c.agent,
                ra.c.slot_name,
                sa.func.sum(effective_amount).label("total_amount"),
            )
            .select_from(ra.join(k, ra.c.kernel_id == k.c.id))
            .where(
                k.c.agent.is_not(None),
                k.c.status.in_(all_resource_statuses),
                ra.c.free_at.is_(None),
            )
            .group_by(k.c.agent, ra.c.slot_name)
        )

    async def compute_actual_agent_resource_usage(
        self,
    ) -> dict[tuple[str, str], Decimal]:
        """Compute actual per-agent per-slot resource usage from resource_allocations.

        Joins resource_allocations → kernels, filtering by:
        - free_at IS NULL (allocation still active)
        - kernel status in resource-occupying or resource-requesting statuses

        Groups by (agent_id, slot_name) and sums COALESCE(used, requested).

        Returns:
            Mapping of (agent_id, slot_name) → actual used amount.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            rows = (await db_sess.execute(self._build_actual_usage_query())).all()
        return {(row.agent, row.slot_name): row.total_amount for row in rows}

    async def reconcile_agent_resources(self) -> list[AgentResourceDrift]:
        """Compare agent_resources.used against actual resource_allocations and correct drift.

        Computes actual per-agent per-slot usage from active allocations (free_at IS NULL),
        compares with tracked agent_resources.used, and UPDATEs any mismatches.
        All reads and writes happen within a single transaction.

        Returns:
            List of drift entries that were detected and corrected.
        """
        ar = AgentResourceRow.__table__
        drifts: list[AgentResourceDrift] = []

        async with self._db.begin_session() as db_sess:
            # Compute actual usage within the same transaction
            actual_rows = (await db_sess.execute(self._build_actual_usage_query())).all()
            actual_usage: dict[tuple[str, str], Decimal] = {
                (row.agent, row.slot_name): row.total_amount for row in actual_rows
            }

            # Fetch tracked values and compare
            tracked_rows = (
                await db_sess.execute(sa.select(ar.c.agent_id, ar.c.slot_name, ar.c.used))
            ).all()

            for row in tracked_rows:
                agent_id = row.agent_id
                slot_name = row.slot_name
                tracked = row.used
                actual = actual_usage.pop((agent_id, slot_name), Decimal(0))
                if tracked != actual:
                    drifts.append(
                        AgentResourceDrift(
                            agent_id=agent_id,
                            slot_name=slot_name,
                            tracked=tracked,
                            actual=actual,
                        )
                    )
                    await db_sess.execute(
                        sa.update(ar)
                        .where(ar.c.agent_id == agent_id, ar.c.slot_name == slot_name)
                        .values(used=actual)
                    )

            # Remaining entries: allocations exist but no agent_resources row (orphaned)
            for (agent_id, slot_name), actual in actual_usage.items():
                drifts.append(
                    AgentResourceDrift(
                        agent_id=agent_id,
                        slot_name=slot_name,
                        tracked=Decimal(0),
                        actual=actual,
                    )
                )

        return drifts

    async def aggregate_occupied_by_project(self, project_id: uuid.UUID) -> ResourceOccupancy:
        """Aggregate active resource occupancy for a project (group).

        Joins resource_allocations → kernels → resource_slot_types.
        Only includes kernels with resource-occupying/requesting statuses and free_at IS NULL.

        Returns:
            ResourceOccupancy with used_slots (sorted by rank) and session_count.
        """
        ra = ResourceAllocationRow.__table__
        k = KernelRow.__table__
        rst = ResourceSlotTypeRow.__table__
        all_resource_statuses = (
            KernelStatus.resource_occupied_statuses() | KernelStatus.resource_requested_statuses()
        )
        effective_amount = sa.func.coalesce(ra.c.used, ra.c.requested)
        common_where = (
            k.c.group_id == project_id,
            k.c.status.in_(all_resource_statuses),
            ra.c.free_at.is_(None),
        )
        slot_stmt = (
            sa.select(
                ra.c.slot_name,
                sa.func.sum(effective_amount).label("total_amount"),
                rst.c.rank,
            )
            .select_from(
                ra.join(k, ra.c.kernel_id == k.c.id).join(rst, ra.c.slot_name == rst.c.slot_name)
            )
            .where(*common_where)
            .group_by(ra.c.slot_name, rst.c.rank)
        )
        count_stmt = (
            sa.select(sa.func.count(sa.distinct(k.c.session_id)).label("session_count"))
            .select_from(ra.join(k, ra.c.kernel_id == k.c.id))
            .where(*common_where)
        )
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            slot_rows = (await db_sess.execute(slot_stmt)).all()
            (session_count,) = (await db_sess.execute(count_stmt)).one()

        rank_map = {row.slot_name: row.rank for row in slot_rows}
        used_slots = sorted(
            [SlotQuantity(slot_name=row.slot_name, quantity=row.total_amount) for row in slot_rows],
            key=lambda sq: rank_map.get(sq.slot_name, 9999),
        )
        return ResourceOccupancy(used_slots=used_slots, session_count=session_count)

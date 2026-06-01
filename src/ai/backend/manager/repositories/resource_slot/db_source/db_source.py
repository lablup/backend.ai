"""Database source for Resource Slot repository operations."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.types import SlotQuantity
from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    AgentResourceDrift,
    AgentResourceSearchResult,
    NumberFormatData,
    OrphanedAllocation,
    ReconciliationResult,
    ResourceAllocationData,
    ResourceAllocationSearchResult,
    ResourceOccupancy,
    ResourceSlotTypeData,
    ResourceSlotTypeSearchResult,
    TerminalSessionKernelReconciliation,
)
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.errors.resource_slot import (
    AgentResourceNotFound,
    ResourceAllocationNotFound,
    ResourceSlotTypeNotFound,
)
from ai.backend.manager.models.kernel import KernelRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.models.session import SessionRow
from ai.backend.manager.models.utils import sql_json_merge
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

    async def get_agent_resource_by_slot(self, agent_id: str, slot_name: str) -> AgentResourceRow:
        """Get a single slot capacity/usage row for a specific agent+slot combination.

        Raises:
            AgentResourceNotFound: If no entry exists for the given agent and slot.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            stmt = sa.select(AgentResourceRow).where(
                AgentResourceRow.agent_id == agent_id,
                AgentResourceRow.slot_name == slot_name,
            )
            result = await db_sess.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                raise AgentResourceNotFound(
                    f"Agent resource not found for agent='{agent_id}', slot='{slot_name}'."
                )
            return row

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
                    reserved=row.AgentResourceRow.reserved,
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

    async def get_kernel_allocation_by_slot(
        self, kernel_id: uuid.UUID, slot_name: str
    ) -> ResourceAllocationRow:
        """Get a single allocation row for a specific kernel+slot combination.

        Raises:
            ResourceAllocationNotFound: If no entry exists for the given kernel and slot.
        """
        async with self._db.begin_readonly_session_read_committed() as db_sess:
            stmt = sa.select(ResourceAllocationRow).where(
                ResourceAllocationRow.kernel_id == kernel_id,
                ResourceAllocationRow.slot_name == slot_name,
            )
            result = await db_sess.execute(stmt)
            row = result.scalar_one_or_none()
            if row is None:
                raise ResourceAllocationNotFound(
                    f"Resource allocation not found for kernel='{kernel_id}', slot='{slot_name}'."
                )
            return row

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

    async def reconcile_agent_resources(self) -> ReconciliationResult:
        """Reconcile kernel/session state and agent_resources usage in one transaction.

        Runs three steps in order within a single transaction. Ordering matters: each
        step relies on the previous step having already normalized the relevant rows.

        1. Sync kernels of terminal sessions — if a kernel is non-terminal but its
           session has reached a terminal status (CANCELLED/TERMINATED/ERROR), pull
           the kernel to the session's terminal status and free its active
           resource_allocations in the same step.
        2. Free stale allocations of terminal kernels — safety net for any already
           terminal kernel whose resource_allocations row still has free_at=NULL
           (e.g. left over from older code paths or step 1's kernels if a write
           race happened).
        3. Correct agent_resources.used — recalculate used against the sum of
           active allocations (free_at IS NULL) and write back drifts. Runs last
           so that steps 1 and 2 have already closed out every allocation that
           should be closed.
        """
        async with self._db.begin_session() as db_sess:
            now = await self._db_now(db_sess)
            reconciled_kernels = await self._finalize_kernels_of_terminal_sessions(db_sess, now)
            orphans = await self._free_stale_allocations_of_terminal_kernels(db_sess)
            drifts = await self._correct_agent_resource_drifts(db_sess)

        return ReconciliationResult(
            reconciled_terminal_kernels=reconciled_kernels,
            orphaned_allocations=orphans,
            agent_resource_drifts=drifts,
        )

    @staticmethod
    async def _db_now(db_sess: SASession) -> datetime:
        """Return the database's current timestamp within an existing session."""
        result = await db_sess.execute(sa.select(sa.func.now()))
        return result.scalar_one()

    async def _finalize_kernels_of_terminal_sessions(
        self,
        db_sess: SASession,
        now: datetime,
    ) -> list[TerminalSessionKernelReconciliation]:
        """Step 1: force-close non-terminal kernels of terminal sessions to
        CANCELLED and free their active resource_allocations in the same call.

        This is abnormal-state cleanup — we do not try to mirror the session's
        specific terminal sub-state onto the kernel. A single CANCELLED target is
        used because the kernel reached this inconsistent state outside of the
        normal scheduling_controller lifecycle and the usual transition rules
        no longer apply.

        The kernel transition and the allocation free-out are one inseparable unit
        of work — if this method returns without an exception, every reconciled
        kernel's active allocations have free_at set.
        """
        k = KernelRow.__table__
        ra = ResourceAllocationRow.__table__
        s = SessionRow.__table__
        kernel_terminal = KernelStatus.terminal_statuses()
        session_terminal = SessionStatus.terminal_statuses()

        drift_rows = (
            await db_sess.execute(
                sa.select(
                    k.c.id.label("kernel_id"),
                    k.c.session_id.label("session_id"),
                    k.c.status.label("from_status"),
                )
                .select_from(k.join(s, k.c.session_id == s.c.id))
                .where(
                    s.c.status.in_(session_terminal),
                    k.c.status.notin_(kernel_terminal),
                )
            )
        ).all()
        if not drift_rows:
            return []

        reconciliations = [
            TerminalSessionKernelReconciliation(
                kernel_id=row.kernel_id,
                session_id=row.session_id,
                from_kernel_status=KernelStatus(row.from_status).value,
            )
            for row in drift_rows
        ]
        reconciled_kernel_ids = [r.kernel_id for r in reconciliations]

        await db_sess.execute(
            sa.update(k)
            .where(k.c.id.in_(reconciled_kernel_ids))
            .values(
                status=KernelStatus.CANCELLED,
                status_info="reconciled: session reached terminal state",
                status_changed=now,
                terminated_at=now,
                status_history=sql_json_merge(
                    k.c.status_history,
                    (),
                    {KernelStatus.CANCELLED.name: now.isoformat()},
                ),
            )
        )
        await db_sess.execute(
            sa.update(ra)
            .where(
                ra.c.kernel_id.in_(reconciled_kernel_ids),
                ra.c.free_at.is_(None),
            )
            .values(free_at=now)
        )
        return reconciliations

    async def _free_stale_allocations_of_terminal_kernels(
        self,
        db_sess: SASession,
    ) -> list[OrphanedAllocation]:
        """Step 2: set free_at on allocations whose kernel is already terminal."""
        k = KernelRow.__table__
        ra = ResourceAllocationRow.__table__
        terminal_statuses = KernelStatus.terminal_statuses()
        result = await db_sess.execute(
            sa.update(ra)
            .where(
                ra.c.free_at.is_(None),
                ra.c.kernel_id.in_(sa.select(k.c.id).where(k.c.status.in_(terminal_statuses))),
            )
            .values(free_at=sa.func.now())
            .returning(ra.c.kernel_id, ra.c.slot_name)
        )
        return [
            OrphanedAllocation(kernel_id=row.kernel_id, slot_name=row.slot_name)
            for row in result.all()
        ]

    async def _correct_agent_resource_drifts(
        self,
        db_sess: SASession,
    ) -> list[AgentResourceDrift]:
        """Step 3: rewrite agent_resources.used to match sum of active allocations."""
        ar = AgentResourceRow.__table__
        drifts: list[AgentResourceDrift] = []

        actual_rows = (await db_sess.execute(self._build_actual_usage_query())).all()
        actual_usage: dict[tuple[str, str], Decimal] = {
            (row.agent, row.slot_name): row.total_amount for row in actual_rows
        }
        tracked_rows = (
            await db_sess.execute(sa.select(ar.c.agent_id, ar.c.slot_name, ar.c.used))
        ).all()

        for row in tracked_rows:
            tracked = row.used
            actual = actual_usage.pop((row.agent_id, row.slot_name), Decimal(0))
            if tracked != actual:
                drifts.append(
                    AgentResourceDrift(
                        agent_id=row.agent_id,
                        slot_name=row.slot_name,
                        tracked=tracked,
                        actual=actual,
                    )
                )
                await db_sess.execute(
                    sa.update(ar)
                    .where(ar.c.agent_id == row.agent_id, ar.c.slot_name == row.slot_name)
                    .values(used=actual)
                )

        # Allocations exist but no agent_resources row — surface as drift for visibility.
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

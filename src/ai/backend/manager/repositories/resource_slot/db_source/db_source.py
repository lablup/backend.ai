"""Database source for Resource Slot repository operations."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.manager.data.kernel.types import KernelStatus
from ai.backend.manager.data.resource_slot.types import AgentResourceDrift
from ai.backend.manager.errors.resource_slot import (
    ResourceSlotTypeNotFound,
)
from ai.backend.manager.models.kernel.row import KernelRow
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
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

    # ==================== Reconciliation ====================

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

"""Database source for Resource Slot repository operations."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, cast

import sqlalchemy as sa
from sqlalchemy.engine import CursorResult

from ai.backend.common.types import AgentId, SlotQuantity
from ai.backend.manager.errors.resource_slot import (
    AgentResourceCapacityExceeded,
    ResourceSlotTypeNotFound,
)
from ai.backend.manager.models.resource_slot import (
    AgentResourceRow,
    ResourceAllocationRow,
    ResourceSlotTypeRow,
)
from ai.backend.manager.repositories.base import (
    BulkUpserter,
    execute_bulk_upserter,
)
from ai.backend.manager.repositories.resource_slot.types import (
    AgentOccupiedSlots,
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

    # ==================== resource_allocations ====================

    async def request_resources(
        self,
        kernel_id: uuid.UUID,
        slots: Sequence[SlotQuantity],
    ) -> int:
        """INSERT allocation rows with requested amounts only.

        No agent involvement at this stage.

        Returns:
            Number of allocation rows created.
        """
        if not slots:
            return 0
        async with self._db.begin_session_read_committed() as db_sess:
            await db_sess.execute(
                sa.insert(ResourceAllocationRow),
                [
                    {"kernel_id": kernel_id, "slot_name": s.slot_name, "requested": s.quantity}
                    for s in slots
                ],
            )
            return len(slots)

    # ==================== resource_allocations + agent_resources ====================

    async def allocate_resources(
        self,
        kernel_id: uuid.UUID,
        agent_id: str,
        slots: Sequence[SlotQuantity],
    ) -> int:
        """Set used values on allocations and increment agent_resources.used.

        Capacity check is performed per-slot; exceeding capacity
        rolls back the entire transaction.

        Returns:
            Number of slots allocated.

        Raises:
            AgentResourceCapacityExceeded: If any slot would exceed agent capacity.
        """
        if not slots:
            return 0
        ar = AgentResourceRow.__table__
        async with self._db.begin_session_read_committed() as db_sess:
            for s in slots:
                await db_sess.execute(
                    sa.update(ResourceAllocationRow)
                    .where(
                        ResourceAllocationRow.kernel_id == kernel_id,
                        ResourceAllocationRow.slot_name == s.slot_name,
                        ResourceAllocationRow.free_at.is_(None),
                    )
                    .values(used=s.quantity, used_at=sa.func.now())
                )
                new_used = ar.c.used + s.quantity
                result = await db_sess.execute(
                    sa.update(ar)
                    .where(
                        ar.c.agent_id == agent_id,
                        ar.c.slot_name == s.slot_name,
                        new_used <= ar.c.capacity,
                    )
                    .values(used=new_used)
                )
                if cast(CursorResult[Any], result).rowcount == 0:
                    raise AgentResourceCapacityExceeded(
                        f"Agent {agent_id}: capacity exceeded for slot '{s.slot_name}'"
                    )
            return len(slots)

    async def free_resources(
        self,
        kernel_id: uuid.UUID,
        agent_id: str,
    ) -> int:
        """Set free_at on allocations and decrement agent_resources.used.

        Returns:
            Number of allocation rows freed.
        """
        ar = AgentResourceRow.__table__
        async with self._db.begin_session_read_committed() as db_sess:
            released = (
                await db_sess.execute(
                    sa.update(ResourceAllocationRow)
                    .where(
                        ResourceAllocationRow.kernel_id == kernel_id,
                        ResourceAllocationRow.free_at.is_(None),
                    )
                    .values(free_at=sa.func.now())
                    .returning(ResourceAllocationRow.slot_name, ResourceAllocationRow.used)
                )
            ).all()
            if not released:
                return 0
            for r in released:
                if r.used is None:
                    continue
                new_used = ar.c.used - r.used
                await db_sess.execute(
                    sa.update(ar)
                    .where(ar.c.agent_id == agent_id, ar.c.slot_name == r.slot_name)
                    .values(used=new_used)
                )
            return len(released)

    # ==================== agent_resources CRUD ====================

    async def upsert_agent_capacity(
        self,
        bulk_upserter: BulkUpserter[AgentResourceRow],
    ) -> int:
        """Bulk UPSERT agent resource capacity rows.

        On INSERT: sets capacity (used defaults to 0).
        On CONFLICT: updates capacity only.

        Args:
            bulk_upserter: BulkUpserter containing agent resource specs to upsert.

        Returns:
            Number of rows upserted.
        """
        async with self._db.begin_session_read_committed() as db_sess:
            result = await execute_bulk_upserter(
                db_sess,
                bulk_upserter,
                index_elements=["agent_id", "slot_name"],
            )
            return result.upserted_count

    # ==================== agent_resources Read ====================

    async def get_agent_occupancy(
        self,
        agent_ids: set[AgentId],
    ) -> list[AgentOccupiedSlots]:
        """Read current used slots per agent from agent_resources.

        Args:
            agent_ids: Set of agent IDs to query.

        Returns:
            List of AgentOccupiedSlots, one per requested agent.
        """
        if not agent_ids:
            return []

        async with self._db.begin_readonly_session_read_committed() as db_sess:
            stmt = sa.select(
                AgentResourceRow.agent_id,
                AgentResourceRow.slot_name,
                AgentResourceRow.used,
            ).where(
                AgentResourceRow.agent_id.in_(agent_ids),
            )
            result = await db_sess.execute(stmt)

            agent_slots: dict[AgentId, list[SlotQuantity]] = {
                agent_id: [] for agent_id in agent_ids
            }
            for row in result:
                agent_slots[AgentId(row.agent_id)].append(
                    SlotQuantity(slot_name=row.slot_name, quantity=row.used)
                )

            return [
                AgentOccupiedSlots(agent_id=aid, slots=slots) for aid, slots in agent_slots.items()
            ]

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

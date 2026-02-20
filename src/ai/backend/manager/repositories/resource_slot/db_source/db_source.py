"""Database source for Resource Slot repository operations."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.manager.data.resource_slot.types import (
    AgentResourceData,
    AgentResourceSearchResult,
    ResourceAllocationData,
    ResourceAllocationSearchResult,
)
from ai.backend.manager.errors.resource_slot import (
    ResourceSlotTypeNotFound,
)
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
            return AgentResourceSearchResult(items=items, total_count=result.total_count)

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
            return ResourceAllocationSearchResult(items=items, total_count=result.total_count)

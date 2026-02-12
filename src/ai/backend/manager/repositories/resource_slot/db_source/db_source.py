"""Database source for Resource Slot repository operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.manager.errors.resource_slot import (
    ResourceSlotTypeNotFound,
)
from ai.backend.manager.models.resource_slot import (
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

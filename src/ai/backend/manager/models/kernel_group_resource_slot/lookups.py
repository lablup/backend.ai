"""Read specs reaching a session from its kernel groups' resource slot rows."""

from __future__ import annotations

from collections.abc import Sequence
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.kernel_group_resource_slot import KernelGroupResourceSlotID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.models.kernel_group.row import KernelGroupRow
from ai.backend.manager.models.kernel_group_resource_slot.row import KernelGroupResourceSlotRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class KernelGroupResourceSlotOwnerLookup(FieldOwnerLookup[KernelGroupResourceSlotID, SessionID]):
    """The session whose kernel group holds a resource slot row."""

    @override
    def build_query(
        self, field_ids: Sequence[KernelGroupResourceSlotID]
    ) -> sa.sql.Select[tuple[KernelGroupResourceSlotID, SessionID]]:
        return (
            sa.select(KernelGroupResourceSlotRow.id, KernelGroupRow.session_id)
            .join(KernelGroupRow, KernelGroupRow.id == KernelGroupResourceSlotRow.kernel_group_id)
            .where(KernelGroupResourceSlotRow.id.in_(field_ids))
        )

    @override
    def to_entity_id(self, value: UUID) -> SessionID:
        return SessionID(value)

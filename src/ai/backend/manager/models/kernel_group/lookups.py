"""Read specs reaching a session from its kernel groups."""

from __future__ import annotations

from collections.abc import Sequence
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.kernel_group import KernelGroupID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.models.kernel_group.row import KernelGroupRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class KernelGroupOwnerLookup(FieldOwnerLookup[KernelGroupID, SessionID]):
    """The session a kernel group belongs to."""

    @override
    def build_query(
        self, field_ids: Sequence[KernelGroupID]
    ) -> sa.sql.Select[tuple[KernelGroupID, SessionID]]:
        return sa.select(KernelGroupRow.id, KernelGroupRow.session_id).where(
            KernelGroupRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID) -> SessionID:
        return SessionID(value)

"""Read specs reaching a session from its kernel groups' environ rows."""

from __future__ import annotations

from collections.abc import Sequence
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.kernel_group_environ import KernelGroupEnvironID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.manager.models.kernel_group.row import KernelGroupRow
from ai.backend.manager.models.kernel_group_environ.row import KernelGroupEnvironRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup


class KernelGroupEnvironOwnerLookup(FieldOwnerLookup[KernelGroupEnvironID, SessionID]):
    """The session whose kernel group holds an environ row."""

    @override
    def build_query(
        self, field_ids: Sequence[KernelGroupEnvironID]
    ) -> sa.sql.Select[tuple[KernelGroupEnvironID, SessionID]]:
        return (
            sa.select(KernelGroupEnvironRow.id, KernelGroupRow.session_id)
            .join(KernelGroupRow, KernelGroupRow.id == KernelGroupEnvironRow.kernel_group_id)
            .where(KernelGroupEnvironRow.id.in_(field_ids))
        )

    @override
    def to_entity_id(self, value: UUID) -> SessionID:
        return SessionID(value)

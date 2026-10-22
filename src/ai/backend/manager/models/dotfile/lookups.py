from collections.abc import Sequence
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.dotfile import DotfileID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.manager.models.dotfile.row import DotfileRow
from ai.backend.manager.models.specs.lookup import RuntimeFieldOwnerLookup


class DotfileOwnerLookup(RuntimeFieldOwnerLookup[DotfileID]):
    """The entity each named dotfile belongs to, read from the type and id on the row."""

    @override
    def build_query(self, field_ids: Sequence[DotfileID]) -> sa.sql.Select[Any]:
        return sa.select(DotfileRow.id, DotfileRow.entity_id, DotfileRow.entity_type).where(
            DotfileRow.id.in_(field_ids)
        )

    @override
    def owner_of(self, entity_type: EntityType, entity_id: UUID) -> RuntimeEntityID:
        return RuntimeEntityID(entity_type, entity_id)

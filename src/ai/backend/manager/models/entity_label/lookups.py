"""Read specs for labels."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.entity_label import EntityLabelID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.specs.lookup import RuntimeFieldOwnerLookup

__all__ = ("EntityLabelOwnerLookup",)


class EntityLabelOwnerLookup(RuntimeFieldOwnerLookup[EntityLabelID]):
    """The entity each of the labels named is on.

    A label goes on any type, so the type is selected third and the owner is built from
    it and the id together.
    """

    @override
    def build_query(self, field_ids: Sequence[EntityLabelID]) -> sa.sql.Select[Any]:
        return sa.select(
            EntityLabelRow.id, EntityLabelRow.entity_id, EntityLabelRow.entity_type
        ).where(EntityLabelRow.id.in_(field_ids))

    @override
    def owner_of(self, entity_type: EntityType, entity_id: UUID) -> RuntimeEntityID:
        return RuntimeEntityID(entity_type, entity_id)

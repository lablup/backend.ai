"""Read specs for labels."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.label import LabelID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.manager.models.label.row import LabelRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup

__all__ = ("LabelOwnerLookup",)


class LabelOwnerLookup(FieldOwnerLookup[LabelID, RuntimeEntityID]):
    """The entity each of the labels named is on.

    The owner's type is a column rather than a literal: a label goes on any type, so
    which one it is is only knowable per row.
    """

    @override
    def build_query(self, field_ids: Sequence[LabelID]) -> sa.sql.Select[Any]:
        return sa.select(LabelRow.id, LabelRow.entity_id, LabelRow.entity_type).where(
            LabelRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, value: UUID, owner_type: EntityType) -> RuntimeEntityID:
        return RuntimeEntityID(owner_type, value)

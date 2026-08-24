"""Read specs for labels."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy import Row

from ai.backend.common.data.entity.label import LabelID
from ai.backend.common.data.entity.types import EntityType, RuntimeEntityID
from ai.backend.manager.models.label.row import LabelRow
from ai.backend.manager.models.specs.lookup import FieldOwnerLookup

__all__ = ("LabelOwnerLookup",)


class LabelOwnerLookup(FieldOwnerLookup[LabelID, RuntimeEntityID]):
    """The entity each of the labels named is on.

    A label goes on any type, so the owner's type is selected beside its id and read off
    the row rather than named as a constant.
    """

    @override
    def build_query(self, field_ids: Sequence[LabelID]) -> sa.sql.Select[Any]:
        return sa.select(LabelRow.id, LabelRow.entity_id, LabelRow.entity_type).where(
            LabelRow.id.in_(field_ids)
        )

    @override
    def to_entity_id(self, row: Row[Any]) -> RuntimeEntityID:
        return RuntimeEntityID(EntityType(row[2]), row[1])

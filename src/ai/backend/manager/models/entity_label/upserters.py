"""Upsert spec for the label repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.entity_label import EntityLabelKey
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import FieldUpserter

__all__ = ("EntityLabelUpserter",)


@dataclass
class EntityLabelUpserter(FieldUpserter[RuntimeEntityID, EntityLabelRow, EntityLabelData]):
    """Put one key on the entity, replacing the value it already carries.

    An upsert rather than an insert because a key holds one value: naming a key the
    entity already has is a caller restating what it should be, not a mistake.
    """

    key: EntityLabelKey
    value: str

    @override
    def row_class(self) -> type[EntityLabelRow]:
        return EntityLabelRow

    @override
    def index_elements(self) -> list[str]:
        return ["entity_type", "entity_id", "key"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self, owner_id: RuntimeEntityID) -> dict[str, Any]:
        return {
            "entity_type": owner_id.entity_type(),
            "entity_id": owner_id,
            "key": self.key,
            "value": self.value,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here rather than left to the column: an upsert writes
        through ``ON CONFLICT DO UPDATE``, which the ORM's ``onupdate`` never sees."""
        return {"value": self.value, "updated_at": sa.func.now()}

    @override
    def to_data(self, row: EntityLabelRow) -> EntityLabelData:
        return row.to_data()

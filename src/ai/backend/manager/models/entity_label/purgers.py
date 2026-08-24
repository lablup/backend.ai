"""Delete spec for the label repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.entity_label import EntityLabelID
from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.specs.purger import FieldPurger
from ai.backend.manager.models.specs.types import ConflictCheck

__all__ = ("EntityLabelPurger",)


@dataclass
class EntityLabelPurger(FieldPurger[EntityLabelRow, EntityLabelData]):
    """Take one label off the entity that owns it.

    Keyed on the label's own id, as every field delete is; which entity answers for it
    is what :class:`EntityLabelOwnerLookup` reads first.
    """

    label_id: EntityLabelID

    @override
    def row_class(self) -> type[EntityLabelRow]:
        return EntityLabelRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EntityLabelRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.label_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: EntityLabelRow) -> EntityLabelData:
        return row.to_data()

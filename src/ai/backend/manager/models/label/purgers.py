"""Delete spec for the label repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.label import LabelID
from ai.backend.manager.data.label.types import LabelData
from ai.backend.manager.models.label.row import LabelRow
from ai.backend.manager.models.specs.purger import FieldPurger
from ai.backend.manager.models.specs.types import ConflictCheck

__all__ = ("LabelPurger",)


@dataclass
class LabelPurger(FieldPurger[LabelRow, LabelData]):
    """Take one label off the entity that owns it.

    Keyed on the label's own id, as every field delete is; which entity answers for it
    is what :class:`LabelOwnerLookup` reads first.
    """

    label_id: LabelID

    @override
    def row_class(self) -> type[LabelRow]:
        return LabelRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return LabelRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.label_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: LabelRow) -> LabelData:
        return row.to_data()

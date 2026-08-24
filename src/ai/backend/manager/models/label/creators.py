"""Insert spec for the label repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.label import LabelID, LabelKey
from ai.backend.common.data.entity.types import RuntimeEntityID
from ai.backend.manager.data.label.types import LabelData
from ai.backend.manager.errors.label import LabelConflict
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.models.label.row import LabelRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

__all__ = ("LabelCreator",)


@dataclass
class LabelCreator(FieldCreator[RuntimeEntityID, LabelRow, LabelData]):
    """Put one ``key=value`` on the entity that owns it.

    The owner is a :class:`RuntimeEntityID` rather than a declared id class: which kind of
    entity is being labeled is known only from what the caller named.
    """

    key: LabelKey
    value: str

    @override
    def field_id(self, row: LabelRow) -> LabelID:
        return row.id

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=LabelConflict(f"Duplicate label: {self.key}={self.value}"),
                constraint_name="uq_labels_label",
            ),
        )

    @override
    def build_row(self, owner_id: RuntimeEntityID) -> LabelRow:
        return LabelRow(
            entity_type=owner_id.entity_type(),
            entity_id=owner_id,
            key=self.key,
            value=self.value,
        )

    @override
    def to_data(self, row: LabelRow) -> LabelData:
        return row.to_data()

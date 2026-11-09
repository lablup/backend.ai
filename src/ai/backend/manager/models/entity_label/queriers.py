"""BulkFieldQuerier implementation for the entity_labels table."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.entity_label.types import EntityLabelData
from ai.backend.manager.models.entity_label.row import EntityLabelRow
from ai.backend.manager.models.specs.querier import BulkFieldQuerier


class BulkEntityLabelQuerier(BulkFieldQuerier[EntityLabelRow, EntityLabelData]):
    """The label rows the caller named."""

    @override
    def row_class(self) -> type[EntityLabelRow]:
        return EntityLabelRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return EntityLabelRow.id

    @override
    def to_data(self, row: EntityLabelRow) -> EntityLabelData:
        return row.to_data()

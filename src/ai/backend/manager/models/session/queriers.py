from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.session.types import SessionEntityData
from ai.backend.manager.models.session.row import SessionRow
from ai.backend.manager.models.session.searchable_fields import SessionSearchableFields
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


class BulkSessionQuerier(BulkEntityQuerier[SessionRow, SessionEntityData]):
    """The sessions the caller named."""

    @override
    def row_class(self) -> type[SessionRow]:
        return SessionRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return SessionRow.id

    @override
    def to_data(self, row: SessionRow) -> SessionEntityData:
        return SessionSearchableFields.own.to_data(row)

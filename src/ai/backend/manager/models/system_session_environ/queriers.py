from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.system_session_environ.types import SystemSessionEnvironData
from ai.backend.manager.models.specs.querier import BulkEntityQuerier
from ai.backend.manager.models.system_session_environ.row import SystemSessionEnvironRow
from ai.backend.manager.models.system_session_environ.searchable_fields import (
    SystemSessionEnvironSearchableFields,
)

__all__ = ("BulkSystemSessionEnvironQuerier",)


class BulkSystemSessionEnvironQuerier(
    BulkEntityQuerier[SystemSessionEnvironRow, SystemSessionEnvironData]
):
    """The system session environ rows the caller named."""

    @override
    def row_class(self) -> type[SystemSessionEnvironRow]:
        return SystemSessionEnvironRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return SystemSessionEnvironRow.id

    @override
    def to_data(self, row: SystemSessionEnvironRow) -> SystemSessionEnvironData:
        return SystemSessionEnvironSearchableFields.own.to_data(row)

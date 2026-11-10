"""DataQuerier implementations for the idle checker repository."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow
from ai.backend.manager.models.idle_checker.searchable_fields import (
    IdleCheckerSearchableFields,
)
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


class BulkIdleCheckerQuerier(BulkEntityQuerier[IdleCheckerRow, IdleCheckerData]):
    """The idle checkers the caller named."""

    @override
    def row_class(self) -> type[IdleCheckerRow]:
        return IdleCheckerRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return IdleCheckerRow.id

    @override
    def to_data(self, row: IdleCheckerRow) -> IdleCheckerData:
        return IdleCheckerSearchableFields.own.to_data(row)

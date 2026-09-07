"""BulkEntityQuerier implementation for the scaling groups table."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.resource_group.types import ResourceGroupData
from ai.backend.manager.models.resource_group.row import ResourceGroupRow
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


class BulkResourceGroupQuerier(BulkEntityQuerier[ResourceGroupRow, ResourceGroupData]):
    """The resource groups the caller named."""

    @override
    def row_class(self) -> type[ResourceGroupRow]:
        return ResourceGroupRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ResourceGroupRow.id

    @override
    def to_data(self, row: ResourceGroupRow) -> ResourceGroupData:
        return row.to_dataclass()

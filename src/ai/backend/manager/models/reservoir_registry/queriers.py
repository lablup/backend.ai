from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryConnectionData
from ai.backend.manager.models.reservoir_registry.row import ReservoirRegistryRow
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


class BulkReservoirRegistryQuerier(
    BulkEntityQuerier[ReservoirRegistryRow, ReservoirRegistryConnectionData]
):
    """The Reservoir registries the caller named."""

    @override
    def row_class(self) -> type[ReservoirRegistryRow]:
        return ReservoirRegistryRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ReservoirRegistryRow.id

    @override
    def to_data(self, row: ReservoirRegistryRow) -> ReservoirRegistryConnectionData:
        return ReservoirRegistryConnectionData(
            id=ArtifactRegistryID(row.id),
            endpoint=row.endpoint,
            access_key=row.access_key,
            secret_key=row.secret_key,
            api_version=row.api_version,
        )

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryConnectionData
from ai.backend.manager.models.reservoir_registry.row import ReservoirRegistryRow
from ai.backend.manager.models.reservoir_registry.searchable_fields import (
    ReservoirRegistrySearchableFields,
)
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


class BulkReservoirRegistryQuerier(
    BulkEntityQuerier[ReservoirRegistryRow, ReservoirRegistryConnectionData]
):
    """The Reservoir registries the caller named, without the name the meta row holds."""

    @override
    def row_class(self) -> type[ReservoirRegistryRow]:
        return ReservoirRegistryRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ReservoirRegistryRow.id

    @override
    def to_data(self, row: ReservoirRegistryRow) -> ReservoirRegistryConnectionData:
        own = ReservoirRegistrySearchableFields.own
        return ReservoirRegistryConnectionData(
            id=ArtifactRegistryID(own.id.read(row)),
            endpoint=own.endpoint.read(row),
            access_key=own.access_key.read(row),
            secret_key=own.secret_key.read(row),
            api_version=own.api_version.read(row),
        )

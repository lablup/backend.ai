"""What a Reservoir registry search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.exception import RelationNotLoadedError
from ai.backend.manager.data.reservoir_registry.types import ReservoirRegistryData
from ai.backend.manager.models.artifact_registries.query_spec import (
    ArtifactRegistryQuerySpec,
)
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow
from ai.backend.manager.models.reservoir_registry.row import ReservoirRegistryRow
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.correlation import ToOneCorrelation
from ai.backend.manager.models.specs.search.field import NestedQueryColumn, QueryColumn


class _ReservoirRegistryOwnColumns(RowDataConverter[ReservoirRegistryRow, ReservoirRegistryData]):
    """The Reservoir registry's own columns. ``name`` is the meta row's, declared in ``nested``."""

    id = QueryColumn(
        ReservoirRegistryRow.id,
        UUIDConditions(ReservoirRegistryRow.id),
        ColumnOrder(ReservoirRegistryRow.id),
    )
    endpoint = QueryColumn(
        ReservoirRegistryRow.endpoint,
        StringConditions(ReservoirRegistryRow.endpoint),
        ColumnOrder(ReservoirRegistryRow.endpoint),
    )
    access_key = QueryColumn(
        ReservoirRegistryRow.access_key,
        StringConditions(ReservoirRegistryRow.access_key),
        ColumnOrder(ReservoirRegistryRow.access_key),
    )
    secret_key = QueryColumn(ReservoirRegistryRow.secret_key, None, None)
    """Sensitive: the plaintext secret the manager authenticates to the registry with."""
    api_version = QueryColumn(
        ReservoirRegistryRow.api_version,
        StringConditions(ReservoirRegistryRow.api_version),
        ColumnOrder(ReservoirRegistryRow.api_version),
    )

    @override
    def to_data(self, row: ReservoirRegistryRow) -> ReservoirRegistryData:
        meta = row.meta
        if meta is None:
            raise RelationNotLoadedError()
        return ReservoirRegistryData(
            id=self.id.read(row),
            name=ArtifactRegistryQuerySpec.own.name.read(meta),
            endpoint=self.endpoint.read(row),
            access_key=self.access_key.read(row),
            secret_key=self.secret_key.read(row),
            api_version=self.api_version.read(row),
        )


class _ReservoirRegistryNestedColumns:
    """The artifact registry row this registry's name lives in."""

    meta = NestedQueryColumn(
        ArtifactRegistryQuerySpec.own,
        ToOneCorrelation(
            ArtifactRegistryRow,
            ReservoirRegistryRow,
            ArtifactRegistryRow.registry_id == ReservoirRegistryRow.id,
        ),
    )


class ReservoirRegistryQuerySpec:
    own = _ReservoirRegistryOwnColumns()
    nested = _ReservoirRegistryNestedColumns

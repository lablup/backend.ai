"""What an artifact registry search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _ArtifactRegistryOwnFields(RowDataConverter[ArtifactRegistryRow, ArtifactRegistryData]):
    """The artifact registry meta row's own columns."""

    id = SearchableField(
        ArtifactRegistryRow.id,
        UUIDConditions(ArtifactRegistryRow.id),
        ColumnOrder(ArtifactRegistryRow.id),
    )
    registry_id = SearchableField(
        ArtifactRegistryRow.registry_id,
        UUIDConditions(ArtifactRegistryRow.registry_id),
        ColumnOrder(ArtifactRegistryRow.registry_id),
    )
    name = SearchableField(
        ArtifactRegistryRow.name,
        StringConditions(ArtifactRegistryRow.name),
        ColumnOrder(ArtifactRegistryRow.name),
    )
    type = SearchableField(
        ArtifactRegistryRow.type,
        EnumConditions(ArtifactRegistryRow.type, ArtifactRegistryType),
        ColumnOrder(ArtifactRegistryRow.type),
    )

    @override
    def to_data(self, row: ArtifactRegistryRow) -> ArtifactRegistryData:
        return ArtifactRegistryData(
            id=ArtifactRegistryID(self.id.read(row)),
            registry_id=self.registry_id.read(row),
            name=self.name.read(row),
            type=ArtifactRegistryType(self.type.read(row)),
        )


class ArtifactRegistrySearchableFields:
    own = _ArtifactRegistryOwnFields()

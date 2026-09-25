"""What an artifact search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactData,
    ArtifactType,
)
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.specs.conditions.boolean import BoolConditions
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.string import StringConditions
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _ArtifactOwnFields(RowDataConverter[ArtifactRow, ArtifactData]):
    """The artifact's own columns."""

    id = SearchableField(
        ArtifactRow.id, UUIDConditions(ArtifactRow.id), ColumnOrder(ArtifactRow.id)
    )
    type = SearchableField(
        ArtifactRow.type,
        EnumConditions(ArtifactRow.type, ArtifactType),
        ColumnOrder(ArtifactRow.type),
    )
    name = SearchableField(
        ArtifactRow.name, StringConditions(ArtifactRow.name), ColumnOrder(ArtifactRow.name)
    )
    registry_id = SearchableField(
        ArtifactRow.registry_id,
        UUIDConditions(ArtifactRow.registry_id),
        ColumnOrder(ArtifactRow.registry_id),
    )
    registry_type = SearchableField(
        ArtifactRow.registry_type,
        StringConditions(ArtifactRow.registry_type),
        ColumnOrder(ArtifactRow.registry_type),
    )
    source_registry_id = SearchableField(
        ArtifactRow.source_registry_id,
        UUIDConditions(ArtifactRow.source_registry_id),
        ColumnOrder(ArtifactRow.source_registry_id),
    )
    source_registry_type = SearchableField(
        ArtifactRow.source_registry_type,
        StringConditions(ArtifactRow.source_registry_type),
        ColumnOrder(ArtifactRow.source_registry_type),
    )
    description = SearchableField(
        ArtifactRow.description,
        StringConditions(ArtifactRow.description),
        ColumnOrder(ArtifactRow.description),
    )
    readonly = SearchableField(
        ArtifactRow.readonly,
        BoolConditions(ArtifactRow.readonly),
        ColumnOrder(ArtifactRow.readonly),
    )
    extra = SearchableField(ArtifactRow.extra, None, None)
    """Impossible: a JSON document of registry-specific metadata."""
    scanned_at = SearchableField(
        ArtifactRow.scanned_at,
        DateTimeConditions(ArtifactRow.scanned_at),
        ColumnOrder(ArtifactRow.scanned_at),
    )
    updated_at = SearchableField(
        ArtifactRow.updated_at,
        DateTimeConditions(ArtifactRow.updated_at),
        ColumnOrder(ArtifactRow.updated_at),
    )
    availability = SearchableField(
        ArtifactRow.availability,
        EnumConditions(ArtifactRow.availability, ArtifactAvailability),
        ColumnOrder(ArtifactRow.availability),
    )

    @override
    def to_data(self, row: ArtifactRow) -> ArtifactData:
        return ArtifactData(
            id=ArtifactID(self.id.read(row)),
            type=self.type.read(row),
            name=self.name.read(row),
            registry_id=self.registry_id.read(row),
            registry_type=ArtifactRegistryType(self.registry_type.read(row)),
            source_registry_id=self.source_registry_id.read(row),
            source_registry_type=ArtifactRegistryType(self.source_registry_type.read(row)),
            description=self.description.read(row),
            availability=ArtifactAvailability(self.availability.read(row)),
            scanned_at=self.scanned_at.read(row),
            updated_at=self.updated_at.read(row),
            readonly=self.readonly.read(row),
            extra=self.extra.read(row),
        )


class ArtifactSearchableFields:
    own = _ArtifactOwnFields()

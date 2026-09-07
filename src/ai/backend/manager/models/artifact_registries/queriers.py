"""Read specs for the artifact registry repository."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.artifact_registries.types import ArtifactRegistryData
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow
from ai.backend.manager.models.specs.querier import BulkEntityQuerier


class BulkArtifactRegistryQuerier(BulkEntityQuerier[ArtifactRegistryRow, ArtifactRegistryData]):
    """The artifact registries the caller named, keyed by the registry id the single get keys on."""

    @override
    def row_class(self) -> type[ArtifactRegistryRow]:
        return ArtifactRegistryRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ArtifactRegistryRow.registry_id

    @override
    def to_data(self, row: ArtifactRegistryRow) -> ArtifactRegistryData:
        return row.to_dataclass()

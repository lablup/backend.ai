"""Lookup specs for the artifact registries table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.lookup import DataLookup


@dataclass
class ArtifactRegistryNameLookup(DataLookup[ArtifactRegistryRow, ArtifactRegistryID]):
    """Reads the artifact registry a name refers to."""

    name: str

    @override
    def row_class(self) -> type[ArtifactRegistryRow]:
        return ArtifactRegistryRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: ArtifactRegistryRow.name == self.name]

    @override
    def to_entity_id(self, row: ArtifactRegistryRow) -> ArtifactRegistryID:
        return row.id

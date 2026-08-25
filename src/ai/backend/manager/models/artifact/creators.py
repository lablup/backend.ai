"""Insert spec for the artifacts table."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.entity.artifact import ArtifactID
from ai.backend.manager.data.artifact.types import ArtifactData, ArtifactType
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ArtifactCreator(GlobalEntityCreator[ArtifactRow, ArtifactData]):
    """Register an artifact scanned from a registry.

    The registry it names is a superadmin-only registration outside the graph, so the
    artifact joins nothing; its own node is what the rows under it point at.
    """

    name: str
    type: ArtifactType
    registry_id: uuid.UUID
    registry_type: ArtifactRegistryType | str
    source_registry_id: uuid.UUID
    source_registry_type: ArtifactRegistryType | str
    readonly: bool = True
    description: str | None = None
    extra: Any | None = None

    @override
    def entity_id(self, row: ArtifactRow) -> ArtifactID:
        return ArtifactID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self) -> ArtifactRow:
        return ArtifactRow(
            name=self.name,
            type=self.type,
            registry_id=self.registry_id,
            registry_type=self.registry_type,
            source_registry_id=self.source_registry_id,
            source_registry_type=self.source_registry_type,
            readonly=self.readonly,
            description=self.description,
            extra=self.extra,
        )

    @override
    def to_data(self, row: ArtifactRow) -> ArtifactData:
        return row.to_dataclass()

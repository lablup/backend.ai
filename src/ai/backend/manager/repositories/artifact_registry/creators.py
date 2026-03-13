"""CreatorSpec implementations for artifact registry entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.models.artifact_registries import ArtifactRegistryRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class ArtifactRegistryCreatorSpec(CreatorSpec[ArtifactRegistryRow]):
    """CreatorSpec for artifact registries."""

    name: str
    registry_id: uuid.UUID
    type: ArtifactRegistryType

    @override
    def build_row(self) -> ArtifactRegistryRow:
        return ArtifactRegistryRow(
            name=self.name,
            registry_id=self.registry_id,
            type=self.type.value,
        )

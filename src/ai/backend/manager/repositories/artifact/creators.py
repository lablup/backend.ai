"""CreatorSpec implementations for artifact entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact.types import ArtifactType
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class ArtifactCreatorSpec(CreatorSpec[ArtifactRow]):
    """CreatorSpec for artifact creation."""

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

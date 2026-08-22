import uuid
from dataclasses import dataclass, field
from typing import override

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.entity.artifact_registry import ArtifactRegistryID
from ai.backend.common.data.entity.types import EntityData
from ai.backend.manager.types import OptionalState


@dataclass
class ArtifactRegistryData(EntityData):
    id: ArtifactRegistryID
    registry_id: uuid.UUID
    name: str
    type: ArtifactRegistryType

    @override
    def entity_id(self) -> ArtifactRegistryID:
        return self.id


@dataclass
class ArtifactRegistryCreatorMeta:
    name: str


@dataclass
class ArtifactRegistryModifierMeta:
    name: OptionalState[str] = field(default_factory=OptionalState.nop)


@dataclass
class ArtifactRegistryListResult:
    """Search result with total count for artifact registries."""

    items: list[ArtifactRegistryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

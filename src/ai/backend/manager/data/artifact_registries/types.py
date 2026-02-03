import uuid
from dataclasses import dataclass, field

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.types import OptionalState


@dataclass
class ArtifactRegistryData:
    id: uuid.UUID
    registry_id: uuid.UUID
    name: str
    type: ArtifactRegistryType


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

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

import uuid
from dataclasses import dataclass

from ai.backend.manager.data.artifact.types import ArtifactRegistryType


@dataclass
class ArtifactRegistryData:
    id: uuid.UUID
    registry_id: uuid.UUID
    name: str
    type: ArtifactRegistryType

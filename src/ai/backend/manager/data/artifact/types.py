import enum
import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.manager.models.artifact import ArtifactType


class ArtifactRegistryType(enum.StrEnum):
    HUGGING_FACE = "huggingface"


@dataclass
class ArtifactData:
    id: uuid.UUID
    name: str
    type: ArtifactType
    description: str
    registry_id: uuid.UUID
    source_registry_id: uuid.UUID
    registry_type: ArtifactRegistryType
    size: int
    created_at: datetime
    updated_at: datetime
    version: str


@dataclass
class ArtifactGroupData:
    name: str
    type: ArtifactType
    description: str

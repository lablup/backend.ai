import enum
import uuid
from dataclasses import dataclass
from datetime import datetime


class ArtifactType(enum.StrEnum):
    MODEL = "MODEL"
    PACKAGE = "PACKAGE"
    IMAGE = "IMAGE"


class ArtifactRegistryType(enum.StrEnum):
    HUGGINGFACE = "huggingface"


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
    authorized: bool


@dataclass
class ArtifactGroupData:
    name: str
    type: ArtifactType
    description: str

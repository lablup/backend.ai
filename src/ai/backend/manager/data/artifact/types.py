import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.manager.models.artifact import ArtifactType


@dataclass
class ArtifactData:
    id: uuid.UUID
    name: str
    type: ArtifactType
    description: str
    registry: str
    source: str
    size: int
    created_at: datetime
    updated_at: datetime
    version: str


@dataclass
class ArtifactGroupData:
    name: str
    type: ArtifactType
    description: str

import uuid
from dataclasses import dataclass
from datetime import datetime

from ai.backend.manager.models.artifact import ArtifactType


@dataclass
class ArtifactData:
    id: uuid.UUID
    name: str
    type: ArtifactType
    created_at: datetime

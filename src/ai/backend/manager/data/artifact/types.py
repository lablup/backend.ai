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


class ArtifactStatus(enum.StrEnum):
    SCANNED = "SCANNED"
    PULLED = "PULLED"
    PULLING = "PULLING"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    AVAILABLE = "AVAILABLE"
    FAILED = "FAILED"


@dataclass
class ArtifactData:
    id: uuid.UUID
    name: str
    type: ArtifactType
    description: str
    readme: str
    registry_id: uuid.UUID
    source_registry_id: uuid.UUID
    registry_type: ArtifactRegistryType
    source_registry_type: ArtifactRegistryType
    size: int
    created_at: datetime
    updated_at: datetime
    authorized: bool
    status: ArtifactStatus


class ArtifactOrderField(enum.StrEnum):
    NAME = "NAME"
    TYPE = "TYPE"
    SIZE = "SIZE"
    CREATED_AT = "CREATED_AT"
    UPDATED_AT = "UPDATED_AT"

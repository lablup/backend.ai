import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


class ArtifactType(enum.StrEnum):
    MODEL = "MODEL"
    PACKAGE = "PACKAGE"
    IMAGE = "IMAGE"


class ArtifactRegistryType(enum.StrEnum):
    HUGGINGFACE = "huggingface"


class ArtifactStatus(enum.StrEnum):
    """
    ArtifactRevision's status.
    """

    SCANNED = "SCANNED"
    PULLING = "PULLING"
    PULLED = "PULLED"
    VERIFYING = "VERIFYING"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    AVAILABLE = "AVAILABLE"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


@dataclass
class ArtifactData:
    id: uuid.UUID
    name: str
    type: ArtifactType
    description: str
    registry_id: uuid.UUID
    source_registry_id: uuid.UUID
    registry_type: ArtifactRegistryType
    source_registry_type: ArtifactRegistryType
    readonly: bool


@dataclass
class ArtifactRevisionData:
    id: uuid.UUID
    artifact_id: uuid.UUID
    version: str
    readme: Optional[str]
    size: Optional[int]
    status: ArtifactStatus
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


# TODO: Should we keep this for REST API?
@dataclass
class ArtifactDataWithRevisions:
    artifact: ArtifactData
    revisions: list[ArtifactRevisionData]


class ArtifactOrderField(enum.StrEnum):
    NAME = "NAME"
    TYPE = "TYPE"
    SIZE = "SIZE"


class ArtifactRevisionOrderField(enum.StrEnum):
    VERSION = "VERSION"
    SIZE = "SIZE"
    CREATED_AT = "CREATED_AT"
    UPDATED_AT = "UPDATED_AT"
    STATUS = "STATUS"

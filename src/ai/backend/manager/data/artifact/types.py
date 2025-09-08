import enum
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Self

from ai.backend.common.data.artifact.types import ArtifactRegistryType


class ArtifactType(enum.StrEnum):
    MODEL = "MODEL"
    PACKAGE = "PACKAGE"
    IMAGE = "IMAGE"


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
    description: Optional[str]
    registry_id: uuid.UUID
    source_registry_id: uuid.UUID
    registry_type: ArtifactRegistryType
    source_registry_type: ArtifactRegistryType
    scanned_at: datetime
    updated_at: datetime
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


@dataclass
class ArtifactDataWithRevisions(ArtifactData):
    revisions: list[ArtifactRevisionData]

    @classmethod
    def from_dataclasses(
        cls, artifact_data: ArtifactData, revisions: list[ArtifactRevisionData]
    ) -> Self:
        return cls(
            id=artifact_data.id,
            name=artifact_data.name,
            type=artifact_data.type,
            description=artifact_data.description,
            registry_id=artifact_data.registry_id,
            source_registry_id=artifact_data.source_registry_id,
            registry_type=artifact_data.registry_type,
            source_registry_type=artifact_data.source_registry_type,
            scanned_at=artifact_data.scanned_at,
            updated_at=artifact_data.updated_at,
            readonly=artifact_data.readonly,
            revisions=revisions,
        )


class ArtifactOrderField(enum.StrEnum):
    NAME = "NAME"
    TYPE = "TYPE"
    SIZE = "SIZE"
    SCANNED_AT = "SCANNED_AT"
    UPDATED_AT = "UPDATED_AT"


class ArtifactRevisionOrderField(enum.StrEnum):
    VERSION = "VERSION"
    SIZE = "SIZE"
    CREATED_AT = "CREATED_AT"
    UPDATED_AT = "UPDATED_AT"
    STATUS = "STATUS"

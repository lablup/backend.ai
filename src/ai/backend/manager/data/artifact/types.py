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


class ArtifactRemoteStatus(enum.StrEnum):
    """
    ArtifactRevision's remote status.

    Only used for tracking remote reservoir registry's artifact statuses.
    """

    SCANNED = "SCANNED"
    AVAILABLE = "AVAILABLE"


class ArtifactAvailability(enum.StrEnum):
    """
    Artifact's availability.
    """

    ALIVE = "ALIVE"
    DELETED = "DELETED"


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
    availability: ArtifactAvailability
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
    remote_status: Optional[ArtifactRemoteStatus]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


@dataclass
class ArtifactRevisionResponseData:
    """ArtifactRevisionData without readme field for API responses."""

    id: uuid.UUID
    artifact_id: uuid.UUID
    version: str
    size: Optional[int]
    status: ArtifactStatus
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def from_revision_data(cls, data: ArtifactRevisionData) -> Self:
        return cls(
            id=data.id,
            artifact_id=data.artifact_id,
            version=data.version,
            size=data.size,
            status=data.status,
            created_at=data.created_at,
            updated_at=data.updated_at,
        )


@dataclass
class ArtifactRevisionReadme:
    readme: Optional[str]


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
            availability=artifact_data.availability,
            revisions=revisions,
        )


@dataclass
class ArtifactDataWithRevisionsResponse(ArtifactData):
    """ArtifactDataWithRevisions without readme in revisions for API responses."""

    revisions: list[ArtifactRevisionResponseData]

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
            availability=artifact_data.availability,
            revisions=[ArtifactRevisionResponseData.from_revision_data(rev) for rev in revisions],
        )

    @classmethod
    def from_artifact_with_revisions(
        cls, artifact_with_revisions: ArtifactDataWithRevisions
    ) -> Self:
        return cls(
            id=artifact_with_revisions.id,
            name=artifact_with_revisions.name,
            type=artifact_with_revisions.type,
            description=artifact_with_revisions.description,
            registry_id=artifact_with_revisions.registry_id,
            source_registry_id=artifact_with_revisions.source_registry_id,
            registry_type=artifact_with_revisions.registry_type,
            source_registry_type=artifact_with_revisions.source_registry_type,
            scanned_at=artifact_with_revisions.scanned_at,
            updated_at=artifact_with_revisions.updated_at,
            readonly=artifact_with_revisions.readonly,
            availability=artifact_with_revisions.availability,
            revisions=[
                ArtifactRevisionResponseData.from_revision_data(rev)
                for rev in artifact_with_revisions.revisions
            ],
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


@dataclass
class DelegateeTarget:
    delegatee_reservoir_id: uuid.UUID
    target_registry_id: uuid.UUID

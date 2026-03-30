import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Self

from ai.backend.common.data.artifact.types import (
    ArtifactRegistryType,
    VerificationStepResult,
)
from ai.backend.manager.data.common.types import StringFilterData


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
    FAILED = "FAILED"


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
    description: str | None
    registry_id: uuid.UUID
    source_registry_id: uuid.UUID
    registry_type: ArtifactRegistryType
    source_registry_type: ArtifactRegistryType
    availability: ArtifactAvailability
    scanned_at: datetime
    updated_at: datetime
    readonly: bool
    extra: dict[str, Any] | None


@dataclass
class ArtifactRevisionData:
    id: uuid.UUID
    artifact_id: uuid.UUID
    version: str
    readme: str | None
    size: int | None
    status: ArtifactStatus
    remote_status: ArtifactRemoteStatus | None
    created_at: datetime | None
    updated_at: datetime | None
    digest: str | None
    verification_result: VerificationStepResult | None


@dataclass
class ArtifactRevisionResponseData:
    """ArtifactRevisionData without readme field for API responses."""

    id: uuid.UUID
    artifact_id: uuid.UUID
    version: str
    size: int | None
    status: ArtifactStatus
    remote_status: ArtifactRemoteStatus | None
    created_at: datetime | None
    updated_at: datetime | None
    digest: str | None
    verification_result: VerificationStepResult | None

    @classmethod
    def from_revision_data(cls, data: ArtifactRevisionData) -> Self:
        return cls(
            id=data.id,
            artifact_id=data.artifact_id,
            version=data.version,
            size=data.size,
            status=data.status,
            remote_status=data.remote_status,
            created_at=data.created_at,
            updated_at=data.updated_at,
            digest=data.digest,
            verification_result=data.verification_result,
        )


@dataclass
class ArtifactRevisionReadme:
    readme: str | None


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
            extra=artifact_data.extra,
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
            extra=artifact_data.extra,
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
            extra=artifact_with_revisions.extra,
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


@dataclass
class ArtifactOrderingOptions:
    """Ordering options for artifact queries."""

    order_by: list[tuple[ArtifactOrderField, bool]] = field(
        default_factory=lambda: [(ArtifactOrderField.NAME, False)]
    )  # (field, desc)


@dataclass
class ArtifactFilterOptions:
    """Filtering options for artifacts."""

    artifact_type: list[ArtifactType] | None = None
    name_filter: StringFilterData | None = None
    registry_filter: StringFilterData | None = None
    source_filter: StringFilterData | None = None
    registry_id: uuid.UUID | None = None
    registry_type: ArtifactRegistryType | None = None
    source_registry_id: uuid.UUID | None = None
    source_registry_type: ArtifactRegistryType | None = None
    availability: list[ArtifactAvailability] | None = None

    # Logical operations
    AND: list["ArtifactFilterOptions"] | None = None
    OR: list["ArtifactFilterOptions"] | None = None
    NOT: list["ArtifactFilterOptions"] | None = None


@dataclass
class ArtifactListResult:
    """Search result with total count and pagination info for artifacts."""

    items: list[ArtifactData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class ArtifactRevisionListResult:
    """Search result with total count and pagination info for artifact revisions."""

    items: list[ArtifactRevisionData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class ArtifactWithRevisionsListResult:
    """Search result with total count and pagination info for artifacts with revisions."""

    items: list[ArtifactDataWithRevisions]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

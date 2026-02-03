import uuid
from dataclasses import dataclass, field
from enum import Enum

from ai.backend.manager.api.gql.base import IntFilter, StringFilter
from ai.backend.manager.data.artifact.types import (
    ArtifactRemoteStatus,
    ArtifactRevisionOrderField,
    ArtifactStatus,
)


@dataclass
class ArtifactRevisionOrderingOptions:
    """Ordering options for artifact revision queries."""

    order_by: list[tuple[ArtifactRevisionOrderField, bool]] = field(
        default_factory=lambda: [(ArtifactRevisionOrderField.CREATED_AT, False)]
    )  # (field, desc)


class ArtifactStatusFilterType(Enum):
    IN = "in"
    EQUALS = "equals"


@dataclass
class ArtifactStatusFilter:
    """Status filter with operation type and values."""

    type: ArtifactStatusFilterType
    values: list[ArtifactStatus]


class ArtifactRemoteStatusFilterType(Enum):
    IN = "in"
    EQUALS = "equals"


@dataclass
class ArtifactRemoteStatusFilter:
    """Remote status filter with operation type and values."""

    type: ArtifactRemoteStatusFilterType
    values: list[ArtifactRemoteStatus]


@dataclass
class ArtifactRevisionFilterOptions:
    """Filtering options for artifact revisions."""

    artifact_id: uuid.UUID | None = None
    status_filter: ArtifactStatusFilter | None = None
    remote_status_filter: ArtifactRemoteStatusFilter | None = None
    version_filter: StringFilter | None = None
    size_filter: IntFilter | None = None

    # Logical operations
    AND: list["ArtifactRevisionFilterOptions"] | None = None
    OR: list["ArtifactRevisionFilterOptions"] | None = None
    NOT: list["ArtifactRevisionFilterOptions"] | None = None

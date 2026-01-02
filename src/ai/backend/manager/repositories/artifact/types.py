import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

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

    artifact_id: Optional[uuid.UUID] = None
    status_filter: Optional[ArtifactStatusFilter] = None
    remote_status_filter: Optional[ArtifactRemoteStatusFilter] = None
    version_filter: Optional[StringFilter] = None
    size_filter: Optional[IntFilter] = None

    # Logical operations
    AND: Optional[list["ArtifactRevisionFilterOptions"]] = None
    OR: Optional[list["ArtifactRevisionFilterOptions"]] = None
    NOT: Optional[list["ArtifactRevisionFilterOptions"]] = None

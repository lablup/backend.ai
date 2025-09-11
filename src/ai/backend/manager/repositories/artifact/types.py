import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.api.gql.base import IntFilter, StringFilter
from ai.backend.manager.data.artifact.types import (
    ArtifactAvailability,
    ArtifactOrderField,
    ArtifactRevisionOrderField,
    ArtifactStatus,
    ArtifactType,
)


@dataclass
class ArtifactOrderingOptions:
    """Ordering options for artifact queries."""

    order_by: list[tuple[ArtifactOrderField, bool]] = field(
        default_factory=lambda: [(ArtifactOrderField.NAME, False)]
    )  # (field, desc)


@dataclass
class ArtifactRevisionOrderingOptions:
    """Ordering options for artifact revision queries."""

    order_by: list[tuple[ArtifactRevisionOrderField, bool]] = field(
        default_factory=lambda: [(ArtifactRevisionOrderField.CREATED_AT, False)]
    )  # (field, desc)


@dataclass
class ArtifactFilterOptions:
    """Filtering options for artifacts."""

    artifact_type: Optional[list[ArtifactType]] = None
    name_filter: Optional[StringFilter] = None
    registry_filter: Optional[StringFilter] = None
    source_filter: Optional[StringFilter] = None
    registry_id: Optional[uuid.UUID] = None
    registry_type: Optional[ArtifactRegistryType] = None
    source_registry_id: Optional[uuid.UUID] = None
    source_registry_type: Optional[ArtifactRegistryType] = None
    availability: Optional[list[ArtifactAvailability]] = None

    # Logical operations
    AND: Optional[list["ArtifactFilterOptions"]] = None
    OR: Optional[list["ArtifactFilterOptions"]] = None
    NOT: Optional[list["ArtifactFilterOptions"]] = None


class ArtifactStatusFilterType(Enum):
    IN = "in"
    EQUALS = "equals"


@dataclass
class ArtifactStatusFilter:
    """Status filter with operation type and values."""

    type: ArtifactStatusFilterType
    values: list[ArtifactStatus]


@dataclass
class ArtifactRevisionFilterOptions:
    """Filtering options for artifact revisions."""

    artifact_id: Optional[uuid.UUID] = None
    status_filter: Optional[ArtifactStatusFilter] = None
    version_filter: Optional[StringFilter] = None
    size_filter: Optional[IntFilter] = None

    # Logical operations
    AND: Optional[list["ArtifactRevisionFilterOptions"]] = None
    OR: Optional[list["ArtifactRevisionFilterOptions"]] = None
    NOT: Optional[list["ArtifactRevisionFilterOptions"]] = None

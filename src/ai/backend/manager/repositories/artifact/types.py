import uuid
from dataclasses import dataclass, field
from typing import Optional

from ai.backend.manager.data.artifact.types import (
    ArtifactOrderField,
    ArtifactRegistryType,
    ArtifactStatus,
    ArtifactType,
)


@dataclass
class ArtifactOrderingOptions:
    """Ordering options for artifact queries."""

    order_by: list[tuple[ArtifactOrderField, bool]] = field(
        default_factory=lambda: [(ArtifactOrderField.CREATED_AT, True)]
    )  # (field, desc)


@dataclass
class ArtifactFilterOptions:
    """Filtering options for artifacts."""

    artifact_type: Optional[ArtifactType] = None
    status: Optional[list[ArtifactStatus]] = None  # Changed to support multiple statuses
    authorized: Optional[bool] = None
    name_filter: Optional[str] = None
    registry_id: Optional[uuid.UUID] = None
    registry_type: Optional[ArtifactRegistryType] = None
    source_registry_id: Optional[uuid.UUID] = None
    source_registry_type: Optional[ArtifactRegistryType] = None

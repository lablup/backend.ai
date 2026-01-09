from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any, Optional, Self

from pydantic import BaseModel, Field

from ai.backend.common.data.artifact.types import ArtifactRegistryType


class ArtifactRegistryStatefulData(BaseModel):
    """Base class for artifact registry stateful data."""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Create instance from dictionary with Pydantic validation."""
        return cls.model_validate(data)

    def to_dict(self) -> Mapping[str, Any]:
        """Convert instance to dictionary with JSON-compatible types."""
        return self.model_dump(mode="json")


class _CommonArtifactRegistryStatefulData(ArtifactRegistryStatefulData):
    """Common fields for all artifact registry stateful data types."""

    id: uuid.UUID = Field(
        description="Primary key from the artifact_registries table representing the unified registry entry",
    )
    registry_id: uuid.UUID = Field(
        description=(
            "Foreign key referencing the type-specific registry table "
            "(huggingface_registries or reservoir_registries) containing detailed configuration"
        ),
    )
    name: str = Field(
        description="Human-readable name of the registry used for display and identification purposes",
    )
    type: ArtifactRegistryType = Field(
        description=(
            "Type of the artifact registry (HUGGINGFACE or RESERVOIR) "
            "determining the registry implementation"
        ),
    )


class HuggingFaceRegistryStatefulData(_CommonArtifactRegistryStatefulData):
    """Stateful data type for HuggingFace registry used in Valkey client."""

    url: str = Field(
        description=(
            "Base URL of the HuggingFace Hub instance (e.g., https://huggingface.co) "
            "used for model and dataset downloads"
        ),
    )
    token: Optional[str] = Field(
        default=None,
        description="Optional authentication token for accessing private HuggingFace repositories and datasets",
    )


class ReservoirRegistryStatefulData(_CommonArtifactRegistryStatefulData):
    """Stateful data type for Reservoir registry used in Valkey client."""

    endpoint: str = Field(
        description=(
            "Endpoint URL of the Backend.AI manager instance "
            "configured as a Reservoir registry for artifact storage"
        ),
    )
    access_key: str = Field(
        description=(
            "Access key credential used for authenticating API requests "
            "when communicating with the Backend.AI manager instance configured as Reservoir registry"
        ),
    )
    secret_key: str = Field(
        description=(
            "Secret key credential used for signing and authenticating API requests "
            "when communicating with the Backend.AI manager instance configured as Reservoir registry"
        ),
    )
    api_version: str = Field(
        description="API version string of the Reservoir service protocol (e.g., 'v1') for compatibility management",
    )

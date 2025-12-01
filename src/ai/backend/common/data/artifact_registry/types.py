from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any, Optional, Self

from pydantic import BaseModel

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

    id: uuid.UUID
    registry_id: uuid.UUID
    name: str
    type: ArtifactRegistryType


class HuggingFaceRegistryStatefulData(_CommonArtifactRegistryStatefulData):
    """Stateful data type for HuggingFace registry used in Valkey client."""

    url: str
    token: Optional[str]


class ReservoirRegistryStatefulData(_CommonArtifactRegistryStatefulData):
    """Stateful data type for Reservoir registry used in Valkey client."""

    endpoint: str
    access_key: str
    secret_key: str
    api_version: str

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Optional, Self


@dataclass
class HuggingFaceRegistryStatefulData:
    """Stateful data type for HuggingFace registry used in Valkey client."""

    id: uuid.UUID
    name: str
    url: str
    token: Optional[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create instance from dictionary, converting string UUID to UUID object."""
        if "id" in data and isinstance(data["id"], str):
            data = {**data, "id": uuid.UUID(data["id"])}
        return cls(**data)


@dataclass
class ReservoirRegistryStatefulData:
    """Stateful data type for Reservoir registry used in Valkey client."""

    id: uuid.UUID
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create instance from dictionary, converting string UUID to UUID object."""
        if "id" in data and isinstance(data["id"], str):
            data = {**data, "id": uuid.UUID(data["id"])}
        return cls(**data)

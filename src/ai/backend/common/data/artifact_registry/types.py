from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass
class HuggingFaceRegistryStatefulData:
    """Stateful data type for HuggingFace registry used in Valkey client."""

    id: uuid.UUID
    name: str
    url: str
    token: Optional[str]


@dataclass
class ReservoirRegistryStatefulData:
    """Stateful data type for Reservoir registry used in Valkey client."""

    id: uuid.UUID
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str

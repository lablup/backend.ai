from __future__ import annotations

import uuid
from dataclasses import dataclass

from ai.backend.common.data.artifact_registry.types import ReservoirRegistryStatefulData


@dataclass
class ReservoirRegistryData:
    id: uuid.UUID
    name: str
    endpoint: str
    access_key: str
    secret_key: str
    api_version: str

    @classmethod
    def from_stateful_data(
        cls, stateful_data: ReservoirRegistryStatefulData
    ) -> ReservoirRegistryData:
        """Convert ReservoirRegistryStatefulData to ReservoirRegistryData."""
        return cls(
            id=stateful_data.id,
            name=stateful_data.name,
            endpoint=stateful_data.endpoint,
            access_key=stateful_data.access_key,
            secret_key=stateful_data.secret_key,
            api_version=stateful_data.api_version,
        )

    def to_stateful_data(self) -> ReservoirRegistryStatefulData:
        """Convert ReservoirRegistryData to ReservoirRegistryStatefulData for caching."""
        return ReservoirRegistryStatefulData(
            id=self.id,
            name=self.name,
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            api_version=self.api_version,
        )

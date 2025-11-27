from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from ai.backend.common.data.artifact_registry.types import HuggingFaceRegistryStatefulData


@dataclass
class HuggingFaceRegistryData:
    id: uuid.UUID
    name: str
    url: str
    token: Optional[str]

    @classmethod
    def from_stateful_data(
        cls, stateful_data: HuggingFaceRegistryStatefulData
    ) -> HuggingFaceRegistryData:
        """Convert HuggingFaceRegistryStatefulData to HuggingFaceRegistryData."""
        return cls(
            id=stateful_data.id,
            name=stateful_data.name,
            url=stateful_data.url,
            token=stateful_data.token,
        )

    def to_stateful_data(self) -> HuggingFaceRegistryStatefulData:
        """Convert HuggingFaceRegistryData to HuggingFaceRegistryStatefulData for caching."""
        return HuggingFaceRegistryStatefulData(
            id=self.id,
            name=self.name,
            url=self.url,
            token=self.token,
        )

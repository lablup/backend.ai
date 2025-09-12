from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from ai.backend.common.types import BinarySize, ResourceSlot


@dataclass
class ResourcePresetData:
    id: UUID
    name: str
    resource_slots: ResourceSlot
    shared_memory: Optional[BinarySize | Decimal]
    scaling_group_name: Optional[str]

    def to_cache(self) -> dict[str, Any]:
        """Serialize to cache-friendly format."""
        return {
            "id": str(self.id),
            "name": self.name,
            "resource_slots": self.resource_slots.to_json(),
            "shared_memory": str(self.shared_memory) if self.shared_memory else None,
            "scaling_group_name": self.scaling_group_name,
        }

    @classmethod
    def from_cache(cls, data: dict[str, Any]) -> ResourcePresetData:
        """Deserialize from cache format."""
        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            resource_slots=ResourceSlot.from_json(data["resource_slots"]),
            shared_memory=BinarySize.from_str(data["shared_memory"])
            if data["shared_memory"]
            else None,
            scaling_group_name=data["scaling_group_name"],
        )

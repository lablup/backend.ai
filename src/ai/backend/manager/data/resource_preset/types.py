from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityData
from ai.backend.common.types import BinarySize, ResourceSlot


@dataclass(frozen=True)
class ResourcePresetSearchResult:
    """Result of searching resource presets."""

    items: list[ResourcePresetData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool


@dataclass
class ResourcePresetData(EntityData):
    id: ResourcePresetID
    name: str
    resource_slots: ResourceSlot
    shared_memory: int | None
    scaling_group_name: str | None

    @override
    def entity_id(self) -> ResourcePresetID:
        return self.id

    def to_cache(self) -> dict[str, Any]:
        """Serialize to cache-friendly format."""
        return {
            "id": str(self.id),
            "name": self.name,
            "resource_slots": self.resource_slots.to_json(),
            "shared_memory": str(self.shared_memory) if self.shared_memory is not None else None,
            "scaling_group_name": self.scaling_group_name,
        }

    @classmethod
    def from_cache(cls, data: dict[str, Any]) -> ResourcePresetData:
        """Deserialize from cache format."""
        return cls(
            id=ResourcePresetID(data["id"]),
            name=data["name"],
            resource_slots=ResourceSlot.from_json(data["resource_slots"]),
            shared_memory=int(BinarySize.from_str(data["shared_memory"]))
            if data["shared_memory"] is not None
            else None,
            scaling_group_name=data["scaling_group_name"],
        )

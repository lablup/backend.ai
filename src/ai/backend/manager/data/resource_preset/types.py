from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityData
from ai.backend.common.types import ResourceSlot


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
    resource_group_name: str | None

    @override
    def entity_id(self) -> ResourcePresetID:
        return self.id

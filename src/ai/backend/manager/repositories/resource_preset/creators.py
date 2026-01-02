from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.repositories.base.creator import CreatorSpec


@dataclass
class ResourcePresetCreatorSpec(CreatorSpec[ResourcePresetRow]):
    """CreatorSpec for resource preset."""

    name: str
    resource_slots: ResourceSlot
    shared_memory: Optional[str]
    scaling_group_name: Optional[str]

    @override
    def build_row(self) -> ResourcePresetRow:
        row = ResourcePresetRow()
        row.name = self.name
        row.resource_slots = self.resource_slots
        row.shared_memory = BinarySize.from_str(self.shared_memory) if self.shared_memory else None
        row.scaling_group_name = self.scaling_group_name
        return row

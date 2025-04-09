from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction
from ai.backend.manager.types import Creator


@dataclass
class ResourcePresetCreator(Creator):
    name: str
    resource_slots: ResourceSlot
    shared_memory: Optional[str]
    scaling_group_name: Optional[str]

    def fields_to_store(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "resource_slots": self.resource_slots,
            "shared_memory": BinarySize.from_str(self.shared_memory)
            if self.shared_memory
            else None,
            "scaling_group_name": self.scaling_group_name,
        }


@dataclass
class CreateResourcePresetAction(ResourcePresetAction):
    creator: ResourcePresetCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "create"


@dataclass
class CreateResourcePresetActionResult(BaseActionResult):
    # TODO: Create ResourcePresetRow type
    resource_preset: ResourcePresetRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.resource_preset.id


# TODO: Create exceptions.

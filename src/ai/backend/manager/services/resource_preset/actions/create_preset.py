from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.services.resource_preset.base import ResourcePresetAction


@dataclass
class CreateResourcePresetInputData:
    resource_slots: ResourceSlot
    shared_memory: Optional[str]
    scaling_group_name: Optional[str]


@dataclass
class CreateResourcePresetAction(ResourcePresetAction):
    name: str
    props: CreateResourcePresetInputData

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    def operation_type(self):
        return "create_resource_preset"


@dataclass
class CreateResourcePresetActionResult(BaseActionResult):
    # TODO: Create ResourcePresetRow type
    resource_preset: ResourcePresetRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.resource_preset.id


# TODO: Create exceptions.

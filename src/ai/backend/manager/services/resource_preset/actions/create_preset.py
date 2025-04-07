from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.services.resource_preset.base import ResourcePresetAction


@dataclass
class CreateResourcePresetInput:
    # TODO: Add types.
    resource_slots: dict[str, Any]
    shared_memory: Optional[str] = None
    scaling_group_name: Optional[str] = None


@dataclass
class CreateResourcePresetAction(ResourcePresetAction):
    name: str
    props: CreateResourcePresetInput

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

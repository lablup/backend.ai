import uuid
from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.services.resource_preset.base import ResourcePresetAction


@dataclass
class ModifyResourcePresetInput:
    # TODO: Add types.
    resource_slots: dict[str, Any]
    name: Optional[str] = None
    shared_memory: Optional[str] = None
    scaling_group_name: Optional[str] = None


@dataclass
class ModifyResourcePresetAction(ResourcePresetAction):
    props: ModifyResourcePresetInput
    id: Optional[uuid.UUID] = None
    name: Optional[str] = None

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.id) if self.id else None

    @override
    def operation_type(self):
        return "modify_resource_preset"


@dataclass
class ModifyResourcePresetActionResult(BaseActionResult):
    # TODO: Create ResourcePresetRow type
    resource_preset: ResourcePresetRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.resource_preset.id


# TODO: Create exceptions.

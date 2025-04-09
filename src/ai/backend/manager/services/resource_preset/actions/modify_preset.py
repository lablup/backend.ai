import uuid
from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction
from ai.backend.manager.types import PartialModifier, TriState


@dataclass
class ResourcePresetModifier(PartialModifier):
    resource_slots: TriState[ResourceSlot] = field(default_factory=TriState[ResourceSlot].nop)
    name: TriState[str] = field(default_factory=TriState[str].nop)
    shared_memory: TriState[BinarySize] = field(default_factory=TriState[BinarySize].nop)
    scaling_group_name: TriState[str] = field(default_factory=TriState[str].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.resource_slots.update_dict(to_update, "resource_slots")
        self.name.update_dict(to_update, "name")
        self.shared_memory.update_dict(to_update, "shared_memory")
        self.scaling_group_name.update_dict(to_update, "scaling_group_name")
        return to_update


@dataclass
class ModifyResourcePresetAction(ResourcePresetAction):
    modifier: ResourcePresetModifier
    id: Optional[uuid.UUID]
    name: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.id) if self.id else None

    @override
    def operation_type(self):
        return "modify"


@dataclass
class ModifyResourcePresetActionResult(BaseActionResult):
    # TODO: Create ResourcePresetRow type
    resource_preset: ResourcePresetRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.resource_preset.id


# TODO: Create exceptions.

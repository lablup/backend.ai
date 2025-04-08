import uuid
from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction
from ai.backend.manager.types import TriState


@dataclass
class ModifyResourcePresetInputData:
    resource_slots: TriState[ResourceSlot] = field(
        default_factory=lambda: TriState.nop("resource_slots")
    )
    name: TriState[str] = field(default_factory=lambda: TriState.nop("name"))
    shared_memory: TriState[str] = field(default_factory=lambda: TriState.nop("shared_memory"))
    scaling_group_name: TriState[str] = field(
        default_factory=lambda: TriState.nop("scaling_group_name")
    )

    def set_attr(self, row: Any) -> None:
        self.resource_slots.set_attr(row)
        self.name.set_attr(row)
        self.shared_memory.set_attr(row)
        self.scaling_group_name.set_attr(row)


@dataclass
class ModifyResourcePresetAction(ResourcePresetAction):
    props: ModifyResourcePresetInputData
    id: Optional[uuid.UUID]
    name: Optional[str]

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

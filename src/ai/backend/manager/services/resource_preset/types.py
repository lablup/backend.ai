from dataclasses import dataclass, field
from typing import Any, Optional, override

from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.types import Creator, OptionalState, PartialModifier, TriState


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
class ResourcePresetModifier(PartialModifier):
    resource_slots: OptionalState[ResourceSlot] = field(
        default_factory=OptionalState[ResourceSlot].nop
    )
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
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

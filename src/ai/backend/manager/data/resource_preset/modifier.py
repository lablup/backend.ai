from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.types import ResourceSlot
from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class ResourcePresetModifier(PartialModifier):
    """Modifier for resource preset operations."""

    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    resource_slots: OptionalState[ResourceSlot] = field(default_factory=OptionalState.nop)
    shared_memory: TriState[int] = field(default_factory=TriState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.resource_slots.update_dict(to_update, "resource_slots")
        self.shared_memory.update_dict(to_update, "shared_memory")
        return to_update

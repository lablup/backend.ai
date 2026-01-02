from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from typing_extensions import override

from ai.backend.common.types import BinarySize, ResourceSlot
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ResourcePresetUpdaterSpec(UpdaterSpec[ResourcePresetRow]):
    """UpdaterSpec for resource preset updates."""

    resource_slots: OptionalState[ResourceSlot] = field(
        default_factory=OptionalState[ResourceSlot].nop
    )
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    shared_memory: TriState[BinarySize] = field(default_factory=TriState[BinarySize].nop)
    scaling_group_name: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[ResourcePresetRow]:
        return ResourcePresetRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.resource_slots.update_dict(to_update, "resource_slots")
        self.name.update_dict(to_update, "name")
        self.shared_memory.update_dict(to_update, "shared_memory")
        self.scaling_group_name.update_dict(to_update, "scaling_group_name")
        return to_update

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class VFSStorageModifier(PartialModifier):
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    host: OptionalState[str] = field(default_factory=OptionalState.nop)
    base_path: OptionalState[str] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.host.update_dict(to_update, "host")
        self.base_path.update_dict(to_update, "base_path")
        return to_update

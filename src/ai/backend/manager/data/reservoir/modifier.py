from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class ReservoirRegistryModifier(PartialModifier):
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    endpoint: OptionalState[str] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.endpoint.update_dict(to_update, "endpoint")
        return to_update

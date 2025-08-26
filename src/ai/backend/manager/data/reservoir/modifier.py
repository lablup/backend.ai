from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class ReservoirRegistryModifier(PartialModifier):
    endpoint: OptionalState[str] = field(default_factory=OptionalState.nop)
    access_key: OptionalState[str] = field(default_factory=OptionalState.nop)
    secret_key: OptionalState[str] = field(default_factory=OptionalState.nop)
    api_version: OptionalState[str] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.endpoint.update_dict(to_update, "endpoint")
        self.access_key.update_dict(to_update, "access_key")
        self.secret_key.update_dict(to_update, "secret_key")
        self.api_version.update_dict(to_update, "api_version")
        return to_update

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class ObjectStorageModifier(PartialModifier):
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    host: OptionalState[str] = field(default_factory=OptionalState.nop)
    access_key: OptionalState[str] = field(default_factory=OptionalState.nop)
    secret_key: OptionalState[str] = field(default_factory=OptionalState.nop)
    endpoint: OptionalState[str] = field(default_factory=OptionalState.nop)
    region: OptionalState[str] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.host.update_dict(to_update, "host")
        self.access_key.update_dict(to_update, "access_key")
        self.secret_key.update_dict(to_update, "secret_key")
        self.endpoint.update_dict(to_update, "endpoint")
        self.region.update_dict(to_update, "region")
        return to_update

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.types import OptionalState, PartialModifier


@dataclass
class HuggingFaceRegistryModifier(PartialModifier):
    url: OptionalState[str] = field(default_factory=OptionalState.nop)
    token: OptionalState[str] = field(default_factory=OptionalState.nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.url.update_dict(to_update, "url")
        self.token.update_dict(to_update, "token")
        return to_update

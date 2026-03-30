from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.types import PartialModifier, TriState


@dataclass
class ArtifactModifier(PartialModifier):
    readonly: TriState[bool] = field(default_factory=TriState[bool].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.readonly.update_dict(to_update, "readonly")
        self.description.update_dict(to_update, "description")
        return to_update

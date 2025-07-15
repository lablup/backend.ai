from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class ContainerRegistryModifier(PartialModifier):
    """Modifier for container registry operations."""
    
    url: OptionalState[str] = field(default_factory=OptionalState.nop)
    registry_name: OptionalState[str] = field(default_factory=OptionalState.nop)
    project: OptionalState[str] = field(default_factory=OptionalState.nop)
    username: OptionalState[str] = field(default_factory=OptionalState.nop)
    password: OptionalState[str] = field(default_factory=OptionalState.nop)
    type: OptionalState[str] = field(default_factory=OptionalState.nop)
    ssl_verify: OptionalState[bool] = field(default_factory=OptionalState.nop)
    
    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.url.update_dict(to_update, "url")
        self.registry_name.update_dict(to_update, "registry_name")
        self.project.update_dict(to_update, "project")
        self.username.update_dict(to_update, "username")
        self.password.update_dict(to_update, "password")
        self.type.update_dict(to_update, "type")
        self.ssl_verify.update_dict(to_update, "ssl_verify")
        return to_update
from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class AuthModifier(PartialModifier):
    """Modifier for authentication-related operations."""
    
    is_active: OptionalState[bool] = field(default_factory=OptionalState.nop)
    domain_name: OptionalState[str] = field(default_factory=OptionalState.nop)
    
    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.is_active.update_dict(to_update, "is_active")
        self.domain_name.update_dict(to_update, "domain_name")
        return to_update


@dataclass
class SSHKeypairModifier(PartialModifier):
    """Modifier for SSH keypair operations."""
    
    public_key: OptionalState[str] = field(default_factory=OptionalState.nop)
    private_key: TriState[str] = field(default_factory=TriState.nop)
    name: TriState[str] = field(default_factory=TriState.nop)
    
    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.public_key.update_dict(to_update, "public_key")
        self.private_key.update_dict(to_update, "private_key")
        self.name.update_dict(to_update, "name")
        return to_update
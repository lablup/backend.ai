from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class KeyPairModifier(PartialModifier):
    """Modifier for keypair operations."""
    
    secret_key: OptionalState[str] = field(default_factory=OptionalState.nop)
    user: OptionalState[UUID] = field(default_factory=OptionalState.nop)
    is_active: OptionalState[bool] = field(default_factory=OptionalState.nop)
    is_admin: OptionalState[bool] = field(default_factory=OptionalState.nop)
    resource_policy: OptionalState[str] = field(default_factory=OptionalState.nop)
    rate_limit: OptionalState[int] = field(default_factory=OptionalState.nop)
    num_queries: OptionalState[int] = field(default_factory=OptionalState.nop)
    ssh_public_key: TriState[str] = field(default_factory=TriState.nop)
    bootstrap_script: TriState[str] = field(default_factory=TriState.nop)
    
    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.secret_key.update_dict(to_update, "secret_key")
        self.user.update_dict(to_update, "user")
        self.is_active.update_dict(to_update, "is_active")
        self.is_admin.update_dict(to_update, "is_admin")
        self.resource_policy.update_dict(to_update, "resource_policy")
        self.rate_limit.update_dict(to_update, "rate_limit")
        self.num_queries.update_dict(to_update, "num_queries")
        self.ssh_public_key.update_dict(to_update, "ssh_public_key")
        self.bootstrap_script.update_dict(to_update, "bootstrap_script")
        return to_update
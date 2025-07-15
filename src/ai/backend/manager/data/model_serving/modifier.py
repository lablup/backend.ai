from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class EndpointModifier(PartialModifier):
    """Modifier for model serving endpoint operations."""
    
    name: OptionalState[str] = field(default_factory=OptionalState.nop)
    model: OptionalState[str] = field(default_factory=OptionalState.nop)
    model_version: OptionalState[int] = field(default_factory=OptionalState.nop)
    resource_group: OptionalState[str] = field(default_factory=OptionalState.nop)
    resource_slots: TriState[dict[str, Any]] = field(default_factory=TriState.nop)
    cluster_mode: OptionalState[str] = field(default_factory=OptionalState.nop)
    cluster_size: OptionalState[int] = field(default_factory=OptionalState.nop)
    environ: TriState[dict[str, str]] = field(default_factory=TriState.nop)
    
    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.model.update_dict(to_update, "model")
        self.model_version.update_dict(to_update, "model_version")
        self.resource_group.update_dict(to_update, "resource_group")
        self.resource_slots.update_dict(to_update, "resource_slots")
        self.cluster_mode.update_dict(to_update, "cluster_mode")
        self.cluster_size.update_dict(to_update, "cluster_size")
        self.environ.update_dict(to_update, "environ")
        return to_update


@dataclass
class RoutingModifier(PartialModifier):
    """Modifier for model serving routing operations."""
    
    endpoint: OptionalState[UUID] = field(default_factory=OptionalState.nop)
    session: OptionalState[UUID] = field(default_factory=OptionalState.nop)
    traffic_ratio: OptionalState[float] = field(default_factory=OptionalState.nop)
    
    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.endpoint.update_dict(to_update, "endpoint")
        self.session.update_dict(to_update, "session")
        self.traffic_ratio.update_dict(to_update, "traffic_ratio")
        return to_update


@dataclass
class EndpointTokenModifier(PartialModifier):
    """Modifier for endpoint token operations."""
    
    token: OptionalState[str] = field(default_factory=OptionalState.nop)
    endpoint: OptionalState[UUID] = field(default_factory=OptionalState.nop)
    session: OptionalState[UUID] = field(default_factory=OptionalState.nop)
    
    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.token.update_dict(to_update, "token")
        self.endpoint.update_dict(to_update, "endpoint")
        self.session.update_dict(to_update, "session")
        return to_update
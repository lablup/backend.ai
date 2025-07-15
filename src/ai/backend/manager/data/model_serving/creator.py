from dataclasses import dataclass
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.manager.types import Creator


@dataclass
class EndpointCreator(Creator):
    """Creator for model serving endpoint operations."""
    
    name: str
    project: UUID
    domain: str
    created_user: UUID
    model: str
    model_version: int = 1
    resource_group: str = "default"
    resource_slots: Optional[dict[str, Any]] = None
    cluster_mode: str = "single-node"
    cluster_size: int = 1
    environ: Optional[dict[str, str]] = None
    
    @override
    def fields_to_store(self) -> dict[str, Any]:
        to_store = {
            "name": self.name,
            "project": self.project,
            "domain": self.domain,
            "created_user": self.created_user,
            "model": self.model,
            "model_version": self.model_version,
            "resource_group": self.resource_group,
            "cluster_mode": self.cluster_mode,
            "cluster_size": self.cluster_size,
        }
        if self.resource_slots is not None:
            to_store["resource_slots"] = self.resource_slots
        if self.environ is not None:
            to_store["environ"] = self.environ
        return to_store


@dataclass
class RoutingCreator(Creator):
    """Creator for model serving routing operations."""
    
    endpoint: UUID
    session: UUID
    traffic_ratio: float = 1.0
    
    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "session": self.session,
            "traffic_ratio": self.traffic_ratio,
        }


@dataclass
class EndpointTokenCreator(Creator):
    """Creator for endpoint token operations."""
    
    token: str
    endpoint: UUID
    session: UUID
    
    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "token": self.token,
            "endpoint": self.endpoint,
            "session": self.session,
        }
from dataclasses import dataclass, field
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.manager.types import OptionalState, PartialModifier, TriState


@dataclass
class DeploymentMetadataModifier(PartialModifier):
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    domain: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    project: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)
    resource_group: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    tag: TriState[str] = field(default_factory=TriState[str].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.domain.update_dict(to_update, "domain")
        self.project.update_dict(to_update, "project")
        self.resource_group.update_dict(to_update, "resource_group")
        self.tag.update_dict(to_update, "tag")
        return to_update


@dataclass
class ReplicaSpecModifier(PartialModifier):
    replica_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        # Use the actual database column name "replicas"
        self.replica_count.update_dict(to_update, "replicas")
        return to_update


@dataclass
class DeploymentNetworkSpecModifier(PartialModifier):
    open_to_public: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    url: TriState[str] = field(default_factory=TriState[str].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.open_to_public.update_dict(to_update, "open_to_public")
        self.url.update_dict(to_update, "url")
        return to_update


@dataclass
class ModelRevisionModifier(PartialModifier):
    """Modifier for model revision - currently focused on model_id updates."""

    model_vfolder_id: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.model_vfolder_id.update_dict(to_update, "model_vfolder_id")
        return to_update


@dataclass
class DeploymentModifier(PartialModifier):
    metadata: Optional[DeploymentMetadataModifier] = None
    replica_spec: Optional[ReplicaSpecModifier] = None
    network: Optional[DeploymentNetworkSpecModifier] = None
    model_revision: Optional[ModelRevisionModifier] = None

    # Accessor property for backward compatibility
    @property
    def model_id(self) -> OptionalState[UUID] | None:
        """Get the model_vfolder_id from model revision modifier."""
        if self.model_revision is None:
            return None
        return self.model_revision.model_vfolder_id

    @override
    def fields_to_update(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        if self.metadata:
            to_update.update(self.metadata.fields_to_update())
        if self.replica_spec:
            to_update.update(self.replica_spec.fields_to_update())
        if self.network:
            to_update.update(self.network.fields_to_update())
        if self.model_revision:
            to_update.update(self.model_revision.fields_to_update())
        return to_update

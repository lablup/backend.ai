"""UpdaterSpec implementations for the deployment (endpoint) entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.models.endpoint import EndpointRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class DeploymentMetadataUpdaterSpec(UpdaterSpec[EndpointRow]):
    """UpdaterSpec for deployment metadata updates."""

    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    domain: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    project: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)
    resource_group: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    tag: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.domain.update_dict(to_update, "domain")
        self.project.update_dict(to_update, "project")
        self.resource_group.update_dict(to_update, "resource_group")
        self.tag.update_dict(to_update, "tag")
        return to_update


@dataclass
class ReplicaSpecUpdaterSpec(UpdaterSpec[EndpointRow]):
    """UpdaterSpec for replica specification updates."""

    replica_count: OptionalState[int] = field(default_factory=OptionalState[int].nop)

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        # Use the actual database column names. The scaling goal is
        # COALESCE(desired_replicas, replicas), so a manual scale must update
        # desired_replicas too; otherwise a stale desired_replicas overrides it.
        self.replica_count.update_dict(to_update, "replicas")
        self.replica_count.update_dict(to_update, "desired_replicas")
        return to_update


@dataclass
class EndpointReplicaGroupUpdaterSpec(UpdaterSpec[EndpointRow]):
    """UpdaterSpec for the endpoint's replica-group pointers: the rollout target group
    (PROVISIONING sets it, PROMOTING clears it) and the serving primary (PROMOTING swaps it)."""

    primary_replica_group_id: OptionalState[ReplicaGroupID] = field(
        default_factory=OptionalState[ReplicaGroupID].nop
    )
    target_replica_group_id: TriState[ReplicaGroupID] = field(
        default_factory=TriState[ReplicaGroupID].nop
    )

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.primary_replica_group_id.update_dict(to_update, "primary_replica_group_id")
        self.target_replica_group_id.update_dict(to_update, "target_replica_group_id")
        return to_update


@dataclass
class DeploymentNetworkSpecUpdaterSpec(UpdaterSpec[EndpointRow]):
    """UpdaterSpec for deployment network specification updates."""

    open_to_public: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    url: TriState[str] = field(default_factory=TriState[str].nop)

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.open_to_public.update_dict(to_update, "open_to_public")
        self.url.update_dict(to_update, "url")
        return to_update


@dataclass
class MountUpdaterSpec(UpdaterSpec[EndpointRow]):
    """UpdaterSpec for mount-related updates."""

    model_vfolder_id: OptionalState[UUID] = field(default_factory=OptionalState[UUID].nop)

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.model_vfolder_id.update_dict(to_update, "model_vfolder_id")
        return to_update


@dataclass
class DeploymentUpdaterSpec(UpdaterSpec[EndpointRow]):
    """Composite UpdaterSpec for deployment updates.

    Combines metadata, replica_spec, network, and mount updates.
    """

    metadata: DeploymentMetadataUpdaterSpec | None = None
    replica_spec: ReplicaSpecUpdaterSpec | None = None
    network: DeploymentNetworkSpecUpdaterSpec | None = None
    mount: MountUpdaterSpec | None = None

    @property
    @override
    def row_class(self) -> type[EndpointRow]:
        return EndpointRow

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        if self.metadata:
            to_update.update(self.metadata.build_values())
        if self.replica_spec:
            to_update.update(self.replica_spec.build_values())
        if self.network:
            to_update.update(self.network.build_values())
        if self.mount:
            to_update.update(self.mount.build_values())
        return to_update

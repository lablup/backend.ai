"""UpdaterSpecs for replica group updates, split by deploy / scaling concern."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class ReplicaGroupDeployUpdaterSpec(UpdaterSpec[ReplicaGroupRow]):
    """Deploy-axis update: revision pointers, rollout lifecycle, traffic weight."""

    # Revision pointers are nullable; ``TriState`` so a rollback can NULL them explicitly.
    current_revision_id: TriState[DeploymentRevisionID] = field(default_factory=TriState.nop)
    target_revision_id: TriState[DeploymentRevisionID] = field(default_factory=TriState.nop)
    lifecycle: OptionalState[ReplicaGroupLifecycle] = field(default_factory=OptionalState.nop)
    traffic_weight: OptionalState[int] = field(default_factory=OptionalState.nop)

    @property
    @override
    def row_class(self) -> type[ReplicaGroupRow]:
        return ReplicaGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        self.current_revision_id.update_dict(values, "current_revision_id")
        self.target_revision_id.update_dict(values, "target_revision_id")
        self.lifecycle.update_dict(values, "lifecycle")
        self.traffic_weight.update_dict(values, "traffic_weight")
        return values


@dataclass
class ReplicaGroupScalingUpdaterSpec(UpdaterSpec[ReplicaGroupRow]):
    """Scaling-axis update: desired replica counts and scaling status."""

    desired_current_replica_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    desired_target_replica_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    scaling_status: OptionalState[ReplicaGroupScalingStatus] = field(
        default_factory=OptionalState.nop
    )

    @property
    @override
    def row_class(self) -> type[ReplicaGroupRow]:
        return ReplicaGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        self.desired_current_replica_count.update_dict(values, "desired_current_replica_count")
        self.desired_target_replica_count.update_dict(values, "desired_target_replica_count")
        self.scaling_status.update_dict(values, "scaling_status")
        return values


@dataclass
class ReplicaGroupLifecycleUpdaterSpec(UpdaterSpec[ReplicaGroupRow]):
    """Lifecycle-reconcile update: the rolling/draining step writes both axes at once —
    the next desired counts + scaling status (re-arm scaling) and the lifecycle transition."""

    lifecycle: OptionalState[ReplicaGroupLifecycle] = field(default_factory=OptionalState.nop)
    desired_current_replica_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    desired_target_replica_count: OptionalState[int] = field(default_factory=OptionalState.nop)
    scaling_status: OptionalState[ReplicaGroupScalingStatus] = field(
        default_factory=OptionalState.nop
    )

    @property
    @override
    def row_class(self) -> type[ReplicaGroupRow]:
        return ReplicaGroupRow

    @override
    def build_values(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        self.lifecycle.update_dict(values, "lifecycle")
        self.desired_current_replica_count.update_dict(values, "desired_current_replica_count")
        self.desired_target_replica_count.update_dict(values, "desired_target_replica_count")
        self.scaling_status.update_dict(values, "scaling_status")
        return values

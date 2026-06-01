"""Internal read-projections of a replica group for coordinators/scheduling."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)


@dataclass
class ReplicaGroupDeploySchedulingView:
    """Replica group deploy-axis information (revision pointers + rollout lifecycle)."""

    group_id: ReplicaGroupID
    deployment_id: DeploymentID
    current_revision_id: DeploymentRevisionID | None
    target_revision_id: DeploymentRevisionID | None
    lifecycle: ReplicaGroupLifecycle
    traffic_weight: int


@dataclass
class ReplicaGroupScalingSchedulingView:
    """Replica group scaling-axis information (desired replica counts + scaling status)."""

    group_id: ReplicaGroupID
    deployment_id: DeploymentID
    desired_current_replica_count: int
    desired_target_replica_count: int
    scaling_status: ReplicaGroupScalingStatus

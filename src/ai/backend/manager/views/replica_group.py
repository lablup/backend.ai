"""Internal read-projections of a replica group for coordinators/scheduling."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupLastHistory,
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


@dataclass
class ReplicaGroupScalingReconcileView:
    """Scaling-reconcile decision slice for one group: desired vs actual replica
    counts (split by revision), the revision pointers, and the last scaling history
    row (for the merge-vs-insert decision). Route-creation context is read later,
    at apply time."""

    group_id: ReplicaGroupID
    deployment_id: DeploymentID
    current_revision_id: DeploymentRevisionID | None
    target_revision_id: DeploymentRevisionID | None
    desired_current_replica_count: int
    desired_target_replica_count: int
    # live = warming (PROVISIONING) or serving (RUNNING & ACTIVE); decides "create more".
    # serving = RUNNING & traffic ACTIVE; decides "scaling complete".
    current_live_replica_count: int
    current_serving_replica_count: int
    target_live_replica_count: int
    target_serving_replica_count: int
    last_history: ReplicaGroupLastHistory | None

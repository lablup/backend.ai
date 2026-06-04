"""Internal read-projections of a replica group for coordinators/scheduling."""

from __future__ import annotations

from dataclasses import dataclass

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerOptions,
    ReplicaGroupLifecycle,
    ReplicaGroupRolloutSpec,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.reconciler.types import LastHistory


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
    """Scaling-reconcile decision slice for one group: desired vs actual replica counts
    (split by revision), the revision pointers, the current scaling status, and the prior
    scaling-history descriptor the coordinator uses to classify retries/timeouts."""

    group_id: ReplicaGroupID
    deployment_id: DeploymentID
    current_revision_id: DeploymentRevisionID | None
    target_revision_id: DeploymentRevisionID | None
    scaling_status: ReplicaGroupScalingStatus
    desired_current_replica_count: int
    desired_target_replica_count: int
    # live = warming (PROVISIONING) or serving (RUNNING & ACTIVE); decides "create more".
    # serving = RUNNING & traffic ACTIVE; decides "scaling complete".
    current_live_replica_count: int
    current_serving_replica_count: int
    target_live_replica_count: int
    target_serving_replica_count: int
    # Latest scaling-history row for this group (None when there is none yet).
    last_history: LastHistory | None
    # The group's deployment handler-keyed policy (timeout/retry), resolved at classify time.
    handler_options: DeploymentHandlerOptions


@dataclass
class ReplicaGroupLifecycleReconcileView:
    """Lifecycle-reconcile decision slice for one group: revision pointers, the current
    desired counts, the rollout step config, the deployment's desired replica count (the
    rollout goal), and the prior lifecycle-history descriptor.

    The stage only runs at scaling_status STABLE, so the desired counts are already realized;
    the rolling/draining handlers step ``desired_*`` toward the goal (bounded by ``rollout``)
    and the scaling reconcile then fills routes to the new desired counts."""

    group_id: ReplicaGroupID
    deployment_id: DeploymentID
    current_revision_id: DeploymentRevisionID | None
    target_revision_id: DeploymentRevisionID | None
    lifecycle: ReplicaGroupLifecycle
    scaling_status: ReplicaGroupScalingStatus
    desired_current_replica_count: int
    desired_target_replica_count: int
    # The rollout goal: the deployment's desired replica count the target revision rolls to.
    deployment_desired_replica_count: int
    rollout: ReplicaGroupRolloutSpec
    last_history: LastHistory | None
    handler_options: DeploymentHandlerOptions

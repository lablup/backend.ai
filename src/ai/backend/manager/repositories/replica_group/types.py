"""Repository-layer input types for replica group reconcile operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.models.replica_group import ReplicaGroupRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.repositories.scheduling_history.creators import (
    ReplicaGroupHistoryCreatorSpec,
)
from ai.backend.manager.views.replica_group import ReplicaGroupScalingReconcileView


@dataclass
class ScalingReconcileFetch:
    """One scaling-reconcile fetch: per-group views plus the DB-sourced current time
    (read in the same session so retry/timeout classification uses a consistent clock)."""

    views: list[ReplicaGroupScalingReconcileView]
    now: datetime


@dataclass
class ReplicaGroupReconcileTransition:
    """One group's status change plus the new history row to record it.

    The db_source turns this into the shared ops ``Transition`` (building the match
    conditions to find the latest prior history); the history creator carries sub_steps.
    """

    history_spec: ReplicaGroupHistoryCreatorSpec
    status_updater: Updater[ReplicaGroupRow] | None = None


@dataclass
class RevisionReplicaCount:
    """Active route counts for one (group, revision): warming+serving vs serving only."""

    live: int
    serving: int


@dataclass
class GroupRouteCreateInstruction:
    """Create ``count`` routes for one group's revision; route context is read at apply time."""

    replica_group_id: ReplicaGroupID
    deployment_id: DeploymentID
    revision_id: DeploymentRevisionID
    count: int


@dataclass
class GroupRouteDrainInstruction:
    """Drain ``count`` serving routes of one group's revision (RUNNING & ACTIVE -> INACTIVE)."""

    replica_group_id: ReplicaGroupID
    revision_id: DeploymentRevisionID
    count: int


@dataclass
class ReplicaGroupScalingReconcileApply:
    """One scaling-reconcile tick's writes, applied in a single transaction.

    Domain changes are counts (route creation context is read, drain targets are
    selected, at apply time); ``transitions`` carry each group's status + history
    (with sub_steps), applied via the shared sokovan ``apply_transition`` op.
    """

    create_instructions: Sequence[GroupRouteCreateInstruction] = field(default_factory=list)
    drain_instructions: Sequence[GroupRouteDrainInstruction] = field(default_factory=list)
    transitions: Sequence[ReplicaGroupReconcileTransition] = field(default_factory=list)

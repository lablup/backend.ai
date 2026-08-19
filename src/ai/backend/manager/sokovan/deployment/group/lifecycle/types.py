"""Info/target-status/decision types for the group lifecycle reconcile stages
(rolling + draining), which step ``desired_*`` toward the goal and advance lifecycle."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.deployment_revision import DeploymentRevisionID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerOptions,
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.reconciler.types import HandlerOutcome, LastHistory
from ai.backend.manager.data.session.options import HandlerPolicyResolver
from ai.backend.manager.sokovan.reconciler.base import (
    BaseReconcilerInfo,
    BaseReconcilerResult,
    BaseReconcilerTargetStatuses,
    ReconcilerDecision,
)
from ai.backend.manager.types import TriState
from ai.backend.manager.views.replica_group import (
    ReplicaGroupAutoscaleReconcileView,
    ReplicaGroupLifecycleReconcileView,
)


@dataclass(frozen=True)
class GroupLifecycleTargetStatuses(BaseReconcilerTargetStatuses):
    """Lifecycle + scaling statuses the stage fetches (AND-ed): a lifecycle step only runs
    once the current scaling step has settled."""

    lifecycles: frozenset[ReplicaGroupLifecycle]
    scaling_statuses: frozenset[ReplicaGroupScalingStatus]


@dataclass(frozen=True)
class GroupReconcileStatus:
    """The (lifecycle, scaling_status) a group transitions to for a given reconcile outcome.
    Carried in a stage's ``transitions`` map so both axes are declared there, not in the applier."""

    lifecycle: ReplicaGroupLifecycle
    scaling_status: ReplicaGroupScalingStatus


@dataclass
class GroupLifecycleReconcileInfo(BaseReconcilerInfo):
    """One fetch's worth of lifecycle-reconcile decision state (per-group views + DB now)."""

    views: list[ReplicaGroupLifecycleReconcileView]
    current_time: datetime

    @override
    def entity_ids(self) -> Sequence[UUID]:
        return [view.group_id for view in self.views]

    @override
    def now(self) -> datetime:
        return self.current_time


@dataclass
class GroupAutoscaleReconcileInfo(BaseReconcilerInfo):
    """One fetch's worth of autoscale-reconcile decision state (per-group views + DB now)."""

    views: list[ReplicaGroupAutoscaleReconcileView]
    current_time: datetime

    @override
    def entity_ids(self) -> Sequence[UUID]:
        return [view.group_id for view in self.views]

    @override
    def now(self) -> datetime:
        return self.current_time


@dataclass
class GroupLifecycleDecision(ReconcilerDecision):
    """Per-group lifecycle step: the handler's outcome plus the next desired counts and
    scaling status to write. The coordinator classifies the outcome into the next lifecycle
    via the stage transitions; the applier writes the counts and records history."""

    replica_group_id: ReplicaGroupID
    deployment_id: DeploymentID
    handler_outcome: HandlerOutcome
    message: str
    from_lifecycle: ReplicaGroupLifecycle
    next_desired_current_replica_count: int
    next_desired_target_replica_count: int
    prior_history: LastHistory | None
    handler_options: DeploymentHandlerOptions
    error_code: str | None = None
    # On rollout convergence the group promotes its target revision to current and clears target.
    next_current_revision_id: TriState[DeploymentRevisionID] = field(default_factory=TriState.nop)
    next_target_revision_id: TriState[DeploymentRevisionID] = field(default_factory=TriState.nop)

    @override
    def entity_id(self) -> UUID:
        return self.replica_group_id

    @override
    def outcome(self) -> HandlerOutcome:
        return self.handler_outcome

    @override
    def last_history(self) -> LastHistory | None:
        return self.prior_history

    @override
    def policy_resolver(self) -> HandlerPolicyResolver:
        return self.handler_options


@dataclass
class GroupLifecycleReconcileResult(BaseReconcilerResult):
    """Per-group lifecycle decisions plus processed/failed counts."""

    lifecycle_decisions: list[GroupLifecycleDecision] = field(default_factory=list)
    processed: int = 0
    failed: int = 0

    @override
    def processed_count(self) -> int:
        return self.processed

    @override
    def failed_count(self) -> int:
        return self.failed

    @override
    def decisions(self) -> Sequence[ReconcilerDecision]:
        return self.lifecycle_decisions

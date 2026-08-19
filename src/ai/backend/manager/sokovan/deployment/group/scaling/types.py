"""Info/target-status types for the group scaling reconcile stage."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import (
    DeploymentHandlerOptions,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.reconciler.types import HandlerOutcome, LastHistory
from ai.backend.manager.data.session.options import HandlerPolicyResolver
from ai.backend.manager.repositories.replica_group.types import (
    GroupRouteCreateInstruction,
    GroupRouteDrainInstruction,
)
from ai.backend.manager.sokovan.reconciler.base import (
    BaseReconcilerInfo,
    BaseReconcilerResult,
    BaseReconcilerTargetStatuses,
    ReconcilerDecision,
)
from ai.backend.manager.views.replica_group import ReplicaGroupScalingReconcileView


@dataclass(frozen=True)
class GroupScalingTargetStatuses(BaseReconcilerTargetStatuses):
    """Scaling statuses the stage fetches and reconciles."""

    scaling_statuses: frozenset[ReplicaGroupScalingStatus]


@dataclass
class GroupScalingReconcileInfo(BaseReconcilerInfo):
    """One fetch's worth of scaling-reconcile decision state (per-group views + DB now)."""

    views: list[ReplicaGroupScalingReconcileView]
    current_time: datetime

    @override
    def entity_ids(self) -> Sequence[UUID]:
        return [view.group_id for view in self.views]

    @override
    def now(self) -> datetime:
        return self.current_time


@dataclass
class GroupScalingDecision(ReconcilerDecision):
    """Per-group handler outcome + message/error + the prior-history descriptor.

    The handler sets ``handler_outcome`` to SUCCESS/FAILURE only; the coordinator refines
    FAILURE from ``last_history_*`` and the stage policy. The applier records the final
    (classified) result with this decision's message/error.
    """

    replica_group_id: ReplicaGroupID
    deployment_id: DeploymentID
    handler_outcome: HandlerOutcome
    message: str
    from_status: ReplicaGroupScalingStatus
    prior_history: LastHistory | None
    handler_options: DeploymentHandlerOptions
    error_code: str | None = None

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
class GroupScalingReconcileResult(BaseReconcilerResult):
    """Decided route changes and per-group decisions plus processed/failed counts."""

    create_instructions: list[GroupRouteCreateInstruction] = field(default_factory=list)
    drain_instructions: list[GroupRouteDrainInstruction] = field(default_factory=list)
    scaling_decisions: list[GroupScalingDecision] = field(default_factory=list)
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
        return self.scaling_decisions

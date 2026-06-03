"""Info/target-status types for the group scaling reconcile stage."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from uuid import UUID

from ai.backend.common.identifier.deployment import DeploymentID
from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import ReplicaGroupScalingStatus
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.repositories.replica_group.types import (
    GroupRouteCreateInstruction,
    GroupRouteDrainInstruction,
)
from ai.backend.manager.sokovan.reconciler.base import (
    BaseReconcilerInfo,
    BaseReconcilerResult,
    BaseReconcilerTargetStatuses,
)
from ai.backend.manager.views.replica_group import ReplicaGroupScalingReconcileView


@dataclass(frozen=True)
class GroupScalingTargetStatuses(BaseReconcilerTargetStatuses):
    """Scaling statuses the stage fetches and reconciles."""

    scaling_statuses: frozenset[ReplicaGroupScalingStatus]


@dataclass
class GroupScalingReconcileInfo(BaseReconcilerInfo):
    """One fetch's worth of scaling-reconcile decision state (per-group views)."""

    views: list[ReplicaGroupScalingReconcileView]

    def entity_ids(self) -> Sequence[UUID]:
        return [view.group_id for view in self.views]


@dataclass
class GroupScalingDecision:
    """Per-group reconcile result + message/error decided by the handler; the applier maps
    it to a status transition and records it verbatim in history."""

    replica_group_id: ReplicaGroupID
    deployment_id: DeploymentID
    result: SchedulingResult
    message: str
    error_code: str | None = None


@dataclass
class GroupScalingReconcileResult(BaseReconcilerResult):
    """Decided route changes and per-group results plus processed/failed counts."""

    create_instructions: list[GroupRouteCreateInstruction] = field(default_factory=list)
    drain_instructions: list[GroupRouteDrainInstruction] = field(default_factory=list)
    decisions: list[GroupScalingDecision] = field(default_factory=list)
    processed: int = 0
    failed: int = 0

    def processed_count(self) -> int:
        return self.processed

    def failed_count(self) -> int:
        return self.failed

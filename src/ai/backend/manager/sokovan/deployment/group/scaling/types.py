"""Info/target-status types for the group scaling reconcile stage."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from ai.backend.manager.data.deployment.types import ReplicaGroupScalingStatus
from ai.backend.manager.sokovan.reconciler.base import (
    BaseReconcilerInfo,
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

"""Group scaling reconcile stage spec paired with its repo-built handler/source/applier."""

from __future__ import annotations

from ai.backend.common.events.event_types.schedule.anycast import (
    DoReconcileProcessEvent,
    DoReconcileProcessIfNeededEvent,
)
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.sokovan.deployment.group.categories import GroupReconcileKind
from ai.backend.manager.sokovan.deployment.group.scaling.applier import GroupScalingApplier
from ai.backend.manager.sokovan.deployment.group.scaling.handlers.reconcile import (
    GroupScalingReconcileHandler,
)
from ai.backend.manager.sokovan.deployment.group.scaling.source import GroupScalingSource
from ai.backend.manager.sokovan.deployment.group.scaling.types import GroupScalingTargetStatuses
from ai.backend.manager.sokovan.reconciler.base import (
    ReconcilerStage,
    ReconcilerStageMetadata,
    ReconcilerStageRegistration,
    ReconcilerTaskSpec,
)


def build_group_scaling_stage(
    replica_group_repository: ReplicaGroupRepository,
) -> ReconcilerStageRegistration:
    reconcile_type = "group_scaling"
    metadata = ReconcilerStageMetadata(
        category=ReplicaGroupHandlerCategory.SCALING,
        kind=GroupReconcileKind.GROUP,
        target_statuses=GroupScalingTargetStatuses(
            scaling_statuses=frozenset({ReplicaGroupScalingStatus.SCALING})
        ),
        name="group_scaling_reconcile",
        phase="scaling_reconcile",
        lock_id=LockID.LOCKID_REPLICA_GROUP_SCALING_RECONCILE,
        transitions={
            SchedulingResult.SUCCESS: ReplicaGroupScalingStatus.STABLE,
            SchedulingResult.NEED_RETRY: ReplicaGroupScalingStatus.SCALING,
            SchedulingResult.EXPIRED: ReplicaGroupScalingStatus.SCALING,
            SchedulingResult.GIVE_UP: ReplicaGroupScalingStatus.SCALING,
        },
    )
    stage = ReconcilerStage(
        handler=GroupScalingReconcileHandler(),
        source=GroupScalingSource(replica_group_repository),
        applier=GroupScalingApplier(replica_group_repository),
        metadata=metadata,
    )
    task_spec = ReconcilerTaskSpec(
        reconcile_type=reconcile_type,
        if_needed_event_factory=DoReconcileProcessIfNeededEvent,
        process_event_factory=DoReconcileProcessEvent,
        short_interval=5.0,
        long_interval=30.0,
    )
    return ReconcilerStageRegistration(
        reconcile_type=reconcile_type,
        stage=stage,
        task_spec=task_spec,
    )

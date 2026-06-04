"""Group draining reconcile stage spec paired with its repo-built handler/source/applier."""

from __future__ import annotations

from ai.backend.common.events.event_types.schedule.anycast import (
    DoReconcileProcessEvent,
    DoReconcileProcessIfNeededEvent,
)
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupLifecycle,
    ReplicaGroupScalingStatus,
)
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.replica_group.repository import ReplicaGroupRepository
from ai.backend.manager.sokovan.deployment.group.categories import GroupReconcileKind
from ai.backend.manager.sokovan.deployment.group.lifecycle.applier import GroupLifecycleApplier
from ai.backend.manager.sokovan.deployment.group.lifecycle.handlers.draining import (
    GroupDrainingHandler,
)
from ai.backend.manager.sokovan.deployment.group.lifecycle.source import GroupLifecycleSource
from ai.backend.manager.sokovan.deployment.group.lifecycle.types import GroupLifecycleTargetStatuses
from ai.backend.manager.sokovan.reconciler.base import (
    ReconcilerStage,
    ReconcilerStageMetadata,
    ReconcilerStageRegistration,
    ReconcilerTaskSpec,
)


def build_group_draining_stage(
    replica_group_repository: ReplicaGroupRepository,
) -> ReconcilerStageRegistration:
    reconcile_type = "group_draining"
    metadata = ReconcilerStageMetadata(
        category=ReplicaGroupHandlerCategory.LIFECYCLE,
        kind=GroupReconcileKind.GROUP,
        target_statuses=GroupLifecycleTargetStatuses(
            lifecycles=frozenset({ReplicaGroupLifecycle.DRAINING}),
            scaling_statuses=frozenset({ReplicaGroupScalingStatus.STABLE}),
        ),
        name="group_draining_reconcile",
        phase="group_draining",
        lock_id=LockID.LOCKID_REPLICA_GROUP_DRAINING_RECONCILE,
        transitions={
            SchedulingResult.SUCCESS: ReplicaGroupLifecycle.DRAINED,
            SchedulingResult.NEED_RETRY: ReplicaGroupLifecycle.DRAINING,
            SchedulingResult.EXPIRED: ReplicaGroupLifecycle.DRAINING,
            SchedulingResult.GIVE_UP: ReplicaGroupLifecycle.DRAINING,
        },
    )
    stage = ReconcilerStage(
        handler=GroupDrainingHandler(),
        source=GroupLifecycleSource(replica_group_repository),
        applier=GroupLifecycleApplier(replica_group_repository),
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

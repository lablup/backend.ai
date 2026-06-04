"""Group rolling reconcile stage spec paired with its repo-built handler/source/applier."""

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
from ai.backend.manager.sokovan.deployment.group.lifecycle.handlers.rolling import (
    GroupRollingHandler,
)
from ai.backend.manager.sokovan.deployment.group.lifecycle.source import GroupLifecycleSource
from ai.backend.manager.sokovan.deployment.group.lifecycle.types import GroupLifecycleTargetStatuses
from ai.backend.manager.sokovan.reconciler.base import (
    ReconcilerStage,
    ReconcilerStageMetadata,
    ReconcilerStageRegistration,
    ReconcilerTaskSpec,
)


def build_group_rolling_stage(
    replica_group_repository: ReplicaGroupRepository,
) -> ReconcilerStageRegistration:
    reconcile_type = "group_rolling"
    metadata = ReconcilerStageMetadata(
        category=ReplicaGroupHandlerCategory.LIFECYCLE,
        kind=GroupReconcileKind.GROUP,
        # Step only once the current step's routes have settled (scaling STABLE).
        target_statuses=GroupLifecycleTargetStatuses(
            lifecycles=frozenset({ReplicaGroupLifecycle.ROLLING}),
            scaling_statuses=frozenset({ReplicaGroupScalingStatus.STABLE}),
        ),
        name="group_rolling_reconcile",
        phase="group_rolling",
        lock_id=LockID.LOCKID_REPLICA_GROUP_ROLLING_RECONCILE,
        transitions={
            SchedulingResult.SUCCESS: ReplicaGroupLifecycle.STABLE,
            SchedulingResult.NEED_RETRY: ReplicaGroupLifecycle.ROLLING,
            SchedulingResult.EXPIRED: ReplicaGroupLifecycle.ROLLING,
            SchedulingResult.GIVE_UP: ReplicaGroupLifecycle.ROLLING,
        },
    )
    stage = ReconcilerStage(
        handler=GroupRollingHandler(),
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

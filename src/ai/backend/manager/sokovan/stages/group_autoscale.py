"""Group autoscale reconcile stage: keep a STABLE serving group's replica count at the
deployment's desired count (steady-state scaling), paired with its repo-built source/applier."""

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
from ai.backend.manager.sokovan.deployment.group.lifecycle.handlers.autoscale import (
    GroupAutoscaleHandler,
)
from ai.backend.manager.sokovan.deployment.group.lifecycle.source import GroupAutoscaleSource
from ai.backend.manager.sokovan.deployment.group.lifecycle.types import (
    GroupLifecycleTargetStatuses,
    GroupReconcileStatus,
)
from ai.backend.manager.sokovan.reconciler.base import (
    ReconcilerStage,
    ReconcilerStageMetadata,
    ReconcilerStageRegistration,
    ReconcilerTaskSpec,
)


def build_group_autoscale_stage(
    replica_group_repository: ReplicaGroupRepository,
) -> ReconcilerStageRegistration:
    reconcile_type = "group_autoscale"
    metadata = ReconcilerStageMetadata(
        category=ReplicaGroupHandlerCategory.LIFECYCLE,
        kind=GroupReconcileKind.GROUP,
        # Steady-state group at rest (scaling STABLE): sync its count to the deployment goal
        # and re-arm scaling when the actual live routes drift from it (e.g. a route died).
        target_statuses=GroupLifecycleTargetStatuses(
            lifecycles=frozenset({ReplicaGroupLifecycle.STABLE}),
            scaling_statuses=frozenset({ReplicaGroupScalingStatus.STABLE}),
        ),
        name="group_autoscale_reconcile",
        phase="group_autoscale",
        lock_id=LockID.LOCKID_REPLICA_GROUP_AUTOSCALE_RECONCILE,
        # Stays STABLE; a count change re-arms scaling so the scaling reconcile fills routes.
        transitions={
            SchedulingResult.SUCCESS: GroupReconcileStatus(
                lifecycle=ReplicaGroupLifecycle.STABLE,
                scaling_status=ReplicaGroupScalingStatus.STABLE,
            ),
            SchedulingResult.NEED_RETRY: GroupReconcileStatus(
                lifecycle=ReplicaGroupLifecycle.STABLE,
                scaling_status=ReplicaGroupScalingStatus.SCALING,
            ),
            SchedulingResult.EXPIRED: GroupReconcileStatus(
                lifecycle=ReplicaGroupLifecycle.STABLE,
                scaling_status=ReplicaGroupScalingStatus.SCALING,
            ),
            SchedulingResult.GIVE_UP: GroupReconcileStatus(
                lifecycle=ReplicaGroupLifecycle.STABLE,
                scaling_status=ReplicaGroupScalingStatus.SCALING,
            ),
        },
    )
    stage = ReconcilerStage(
        handler=GroupAutoscaleHandler(),
        source=GroupAutoscaleSource(replica_group_repository),
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

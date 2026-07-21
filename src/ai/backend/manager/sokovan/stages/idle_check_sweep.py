"""Idle-check expiry sweep reconcile stage."""

from __future__ import annotations

from collections.abc import Mapping

from ai.backend.common.events.event_types.schedule.anycast import (
    DoReconcileProcessEvent,
    DoReconcileProcessIfNeededEvent,
)
from ai.backend.manager.data.session.types import SchedulingResult, SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.sokovan.idle_check.handlers.sweep import IdleCheckSweepHandler
from ai.backend.manager.sokovan.idle_check.sweep.applier import IdleCheckSweepApplier
from ai.backend.manager.sokovan.idle_check.sweep.source import IdleCheckSweepSource
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckCategory,
    IdleCheckKind,
    IdleCheckTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import (
    ReconcilerStage,
    ReconcilerStageMetadata,
    ReconcilerStageRegistration,
    ReconcilerTaskSpec,
)
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController


def build_idle_check_sweep_stage(
    idle_checker_repository: IdleCheckerRepository,
    scheduling_controller: SchedulingController,
) -> ReconcilerStageRegistration:
    reconcile_type = "idle_check_sweep"
    transitions: Mapping[SchedulingResult, SessionStatus] = {}
    metadata = ReconcilerStageMetadata(
        category=IdleCheckCategory.IDLE,
        kind=IdleCheckKind.SESSION,
        target_statuses=IdleCheckTargetStatuses(
            session_statuses=frozenset({SessionStatus.RUNNING}),
        ),
        name="idle_check_sweep_reconcile",
        phase="idle_check_sweep",
        lock_id=LockID.LOCKID_IDLE_CHECK_SWEEP_RECONCILE,
        transitions=transitions,
    )
    stage = ReconcilerStage(
        handler=IdleCheckSweepHandler(scheduling_controller),
        source=IdleCheckSweepSource(idle_checker_repository),
        applier=IdleCheckSweepApplier(),
        metadata=metadata,
    )
    task_spec = ReconcilerTaskSpec(
        reconcile_type=reconcile_type,
        if_needed_event_factory=DoReconcileProcessIfNeededEvent,
        process_event_factory=DoReconcileProcessEvent,
        long_interval=10.0,
    )
    return ReconcilerStageRegistration(
        reconcile_type=reconcile_type,
        stage=stage,
        task_spec=task_spec,
    )

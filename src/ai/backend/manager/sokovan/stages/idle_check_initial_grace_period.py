"""Idle-check initial grace period reconcile stage."""

from __future__ import annotations

from collections.abc import Mapping

from ai.backend.common.events.event_types.schedule.anycast import (
    DoReconcileProcessEvent,
    DoReconcileProcessIfNeededEvent,
)
from ai.backend.manager.data.session.types import SchedulingResult, SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.sokovan.idle_check.handlers.initial_grace_period import (
    IdleCheckInitialGracePeriodHandler,
)
from ai.backend.manager.sokovan.idle_check.initial_grace_period.applier import (
    IdleCheckInitialGracePeriodApplier,
)
from ai.backend.manager.sokovan.idle_check.initial_grace_period.source import (
    IdleCheckInitialGracePeriodSource,
)
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


def build_idle_check_initial_grace_period_stage(
    idle_checker_repository: IdleCheckerRepository,
) -> ReconcilerStageRegistration:
    reconcile_type = "idle_check_initial_grace_period"
    transitions: Mapping[SchedulingResult, SessionStatus] = {}
    metadata = ReconcilerStageMetadata(
        category=IdleCheckCategory.SESSION_IDLE_CHECK,
        kind=IdleCheckKind.SESSION,
        target_statuses=IdleCheckTargetStatuses(
            session_statuses=frozenset({SessionStatus.RUNNING}),
        ),
        name="idle_check_initial_grace_period_reconcile",
        phase="initial_grace_period",
        lock_id=LockID.LOCKID_IDLE_CHECK_INITIAL_GRACE_PERIOD_RECONCILE,
        transitions=transitions,
    )
    stage = ReconcilerStage(
        handler=IdleCheckInitialGracePeriodHandler(),
        source=IdleCheckInitialGracePeriodSource(idle_checker_repository),
        applier=IdleCheckInitialGracePeriodApplier(idle_checker_repository),
        metadata=metadata,
    )
    task_spec = ReconcilerTaskSpec(
        reconcile_type=reconcile_type,
        if_needed_event_factory=DoReconcileProcessIfNeededEvent,
        process_event_factory=DoReconcileProcessEvent,
        short_interval=10.0,
        long_interval=60.0,
    )
    return ReconcilerStageRegistration(
        reconcile_type=reconcile_type,
        stage=stage,
        task_spec=task_spec,
    )

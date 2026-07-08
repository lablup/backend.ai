"""Idle-check reconcile stage spec paired with its no-op source/handler/applier."""

from __future__ import annotations

from collections.abc import Mapping

from ai.backend.common.events.event_types.schedule.anycast import (
    DoReconcileProcessEvent,
    DoReconcileProcessIfNeededEvent,
)
from ai.backend.manager.data.session.types import SchedulingResult, SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.sokovan.idle_check.applier import IdleCheckApplier
from ai.backend.manager.sokovan.idle_check.checkers.base import IdleCheckContext
from ai.backend.manager.sokovan.idle_check.handlers.reconcile import IdleCheckReconcileHandler
from ai.backend.manager.sokovan.idle_check.source import IdleCheckSource
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


def build_idle_check_stage(
    idle_checker_repository: IdleCheckerRepository,
) -> ReconcilerStageRegistration:
    reconcile_type = "idle_check"
    # Termination runs through the scheduler lifecycle (mark_sessions_for_termination in
    # the applier) — which also terminates kernels, is idempotent for already-terminating/
    # terminal sessions, and broadcasts — not this per-entity status-transition map.
    transitions: Mapping[SchedulingResult, SessionStatus] = {}
    metadata = ReconcilerStageMetadata(
        category=IdleCheckCategory.IDLE,
        kind=IdleCheckKind.SESSION,
        target_statuses=IdleCheckTargetStatuses(
            session_statuses=frozenset({SessionStatus.RUNNING}),
        ),
        name="idle_check_reconcile",
        phase="idle_check",
        lock_id=LockID.LOCKID_IDLE_CHECK_RECONCILE,
        transitions=transitions,
    )
    stage = ReconcilerStage(
        handler=IdleCheckReconcileHandler(),
        source=IdleCheckSource(idle_checker_repository, IdleCheckContext()),
        applier=IdleCheckApplier(),
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

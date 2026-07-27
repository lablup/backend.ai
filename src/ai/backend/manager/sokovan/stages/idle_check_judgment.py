"""Idle-check judgment reconcile stage."""

from __future__ import annotations

from collections.abc import Mapping

from ai.backend.common.clients.valkey_client.valkey_live.client import ValkeyLiveClient
from ai.backend.common.data.idle_checker.types import CheckerType
from ai.backend.common.events.event_types.schedule.anycast import (
    DoReconcileProcessEvent,
    DoReconcileProcessIfNeededEvent,
)
from ai.backend.manager.data.session.types import SchedulingResult, SessionStatus
from ai.backend.manager.defs import LockID
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.metric.repository import MetricRepository
from ai.backend.manager.services.metric.service import MetricService
from ai.backend.manager.sokovan.idle_check.applier import IdleCheckApplier
from ai.backend.manager.sokovan.idle_check.checkers.base import IdleChecker
from ai.backend.manager.sokovan.idle_check.checkers.network_timeout import NetworkTimeoutChecker
from ai.backend.manager.sokovan.idle_check.checkers.session_lifetime import (
    SessionLifetimeChecker,
)
from ai.backend.manager.sokovan.idle_check.checkers.utilization import UtilizationChecker
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


def build_idle_check_judgment_stage(
    idle_checker_repository: IdleCheckerRepository,
    valkey_live: ValkeyLiveClient,
    metric_repository: MetricRepository,
) -> ReconcilerStageRegistration:
    reconcile_type = "idle_check_judgment"
    # Termination runs through the scheduler lifecycle (mark_sessions_for_termination in
    # the sweep stage handler) — which also terminates kernels, is idempotent for
    # already-terminating/terminal sessions, and broadcasts — not this per-entity
    # status-transition map.
    transitions: Mapping[SchedulingResult, SessionStatus] = {}
    metadata = ReconcilerStageMetadata(
        category=IdleCheckCategory.SESSION_IDLE_CHECK,
        kind=IdleCheckKind.SESSION,
        target_statuses=IdleCheckTargetStatuses(
            session_statuses=frozenset({SessionStatus.RUNNING}),
        ),
        name="idle_check_judgment_reconcile",
        phase="judgment",
        lock_id=LockID.LOCKID_IDLE_CHECK_JUDGMENT_RECONCILE,
        transitions=transitions,
    )
    checkers: Mapping[CheckerType, IdleChecker] = {
        CheckerType.SESSION_LIFETIME: SessionLifetimeChecker(),
        CheckerType.NETWORK_TIMEOUT: NetworkTimeoutChecker(valkey_live),
        CheckerType.UTILIZATION: UtilizationChecker(MetricService(metric_repository)),
    }
    stage = ReconcilerStage(
        handler=IdleCheckReconcileHandler(checkers),
        source=IdleCheckSource(idle_checker_repository),
        applier=IdleCheckApplier(idle_checker_repository),
        metadata=metadata,
    )
    task_spec = ReconcilerTaskSpec(
        reconcile_type=reconcile_type,
        if_needed_event_factory=DoReconcileProcessIfNeededEvent,
        process_event_factory=DoReconcileProcessEvent,
        long_interval=30.0,
    )
    return ReconcilerStageRegistration(
        reconcile_type=reconcile_type,
        stage=stage,
        task_spec=task_spec,
    )

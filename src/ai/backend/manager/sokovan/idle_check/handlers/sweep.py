"""Handler for grouping elapsed idle-check deadlines by session."""

from __future__ import annotations

from typing import override

from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.manager.sokovan.idle_check.sweep.types import (
    IdleCheckSweepReconcileInfo,
    IdleCheckSweepResult,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController


class IdleCheckSweepHandler(ReconcilerHandler[IdleCheckSweepReconcileInfo, IdleCheckSweepResult]):
    """Group stored due rows and request their session termination."""

    _scheduling_controller: SchedulingController

    def __init__(self, scheduling_controller: SchedulingController) -> None:
        self._scheduling_controller = scheduling_controller

    @override
    async def execute(self, reconcile_info: IdleCheckSweepReconcileInfo) -> IdleCheckSweepResult:
        session_ids = list(dict.fromkeys(check.session_id for check in reconcile_info.batch.checks))
        if session_ids:
            await self._scheduling_controller.mark_sessions_for_termination(
                session_ids,
                reason=KernelLifecycleEventReason.IDLE_TIMEOUT.value,
                message="idle check timeout",
            )
        return IdleCheckSweepResult(session_ids=session_ids)

    @override
    async def post_process(self, result: IdleCheckSweepResult) -> None:
        pass

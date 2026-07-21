"""Handler for grouping elapsed idle-check deadlines by session."""

from __future__ import annotations

from collections import defaultdict
from typing import override

from ai.backend.common.events.event_types.kernel.types import KernelLifecycleEventReason
from ai.backend.common.types import SessionId
from ai.backend.manager.sokovan.idle_check.sweep.types import (
    IdleCheckSweepReason,
    IdleCheckSweepReconcileInfo,
    IdleCheckSweepReport,
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
        reasons_by_session: defaultdict[SessionId, list[IdleCheckSweepReason]] = defaultdict(list)
        for check in reconcile_info.batch.checks:
            reasons_by_session[check.session_id].append(
                IdleCheckSweepReason(
                    checker_id=check.checker_id,
                    expire_at=check.expire_at,
                    last_message=check.last_message,
                )
            )
        reports = [
            IdleCheckSweepReport(
                session_id=session_id,
                reasons=reasons,
            )
            for session_id, reasons in reasons_by_session.items()
        ]
        if reports:
            await self._scheduling_controller.mark_sessions_for_termination(
                [report.session_id for report in reports],
                reason=KernelLifecycleEventReason.IDLE_TIMEOUT.value,
                message="idle check timeout",
            )
        return IdleCheckSweepResult(reports=reports)

    @override
    async def post_process(self, result: IdleCheckSweepResult) -> None:
        pass

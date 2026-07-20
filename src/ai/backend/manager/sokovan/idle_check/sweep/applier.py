"""Applier for transitioning sessions with elapsed idle deadlines."""

from __future__ import annotations

import json
from typing import override

from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.scheduler.types.session import IdleCheckTerminationData
from ai.backend.manager.sokovan.idle_check.sweep.types import IdleCheckSweepResult
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckCategory,
    IdleCheckKind,
    IdleCheckTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerApplier, ReconcilerApplyInput
from ai.backend.manager.sokovan.scheduling_controller import SchedulingController

_IdleCheckSweepApplyInput = ReconcilerApplyInput[
    IdleCheckSweepResult,
    IdleCheckCategory,
    IdleCheckKind,
    IdleCheckTargetStatuses,
    SessionStatus,
]


class IdleCheckSweepApplier(
    ReconcilerApplier[
        IdleCheckSweepResult,
        IdleCheckCategory,
        IdleCheckKind,
        IdleCheckTargetStatuses,
        SessionStatus,
    ]
):
    _scheduling_controller: SchedulingController

    def __init__(self, scheduling_controller: SchedulingController) -> None:
        self._scheduling_controller = scheduling_controller

    @override
    async def apply(self, apply_input: _IdleCheckSweepApplyInput) -> None:
        reports = apply_input.result.reports
        if not reports:
            return
        data = [
            IdleCheckTerminationData(
                session_id=report.session_id,
                history_message=json.dumps(
                    {
                        "idle_checks": [
                            {
                                "checker_id": str(reason.checker_id),
                                "last_message": reason.last_message,
                            }
                            for reason in sorted(
                                report.reasons,
                                key=lambda item: str(item.checker_id),
                            )
                        ]
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
            )
            for report in reports
        ]
        await self._scheduling_controller.mark_idle_check_sessions_for_termination(data)

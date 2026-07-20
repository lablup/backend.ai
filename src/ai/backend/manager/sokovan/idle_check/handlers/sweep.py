"""Handler for grouping elapsed idle-check deadlines by session."""

from __future__ import annotations

from collections import defaultdict
from typing import override

from ai.backend.common.types import SessionId
from ai.backend.manager.sokovan.idle_check.sweep.types import (
    IdleCheckSweepReason,
    IdleCheckSweepReconcileInfo,
    IdleCheckSweepReport,
    IdleCheckSweepResult,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler


class IdleCheckSweepHandler(ReconcilerHandler[IdleCheckSweepReconcileInfo, IdleCheckSweepResult]):
    """Group stored due rows without re-running idle checkers."""

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
        return IdleCheckSweepResult(
            reports=[
                IdleCheckSweepReport(
                    session_id=session_id,
                    reasons=reasons,
                )
                for session_id, reasons in reasons_by_session.items()
            ]
        )

    @override
    async def post_process(self, result: IdleCheckSweepResult) -> None:
        pass

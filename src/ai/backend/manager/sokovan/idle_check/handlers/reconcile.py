from __future__ import annotations

from typing import override

from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckReconcileInfo,
    IdleCheckResult,
    IdleVerdict,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler


class IdleCheckReconcileHandler(ReconcilerHandler[IdleCheckReconcileInfo, IdleCheckResult]):
    """Turns prepared checks into idle verdicts; performs no external I/O."""

    @override
    async def execute(self, reconcile_info: IdleCheckReconcileInfo) -> IdleCheckResult:
        verdicts: list[IdleVerdict] = []
        for target in reconcile_info.targets:
            # Evaluate every checker so the verdict lists all that judged the session idle.
            idle_checker_ids: list[IdleCheckerID] = []
            for checker_with_state in target.checkers:
                if checker_with_state.check_idle(target.session_id):
                    idle_checker_ids.append(checker_with_state.checker_id)
            if not idle_checker_ids:
                continue
            verdicts.append(IdleVerdict(session_id=target.session_id, checker_ids=idle_checker_ids))
        return IdleCheckResult(verdicts=verdicts)

    @override
    async def post_process(self, result: IdleCheckResult) -> None:
        pass

from __future__ import annotations

from typing import override

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
            # First idle verdict in resolved order wins; at most one termination per session.
            for checker_with_state in target.checkers:
                if checker_with_state.check_idle(target.session_id):
                    verdicts.append(
                        IdleVerdict(
                            session_id=target.session_id,
                            checker_id=checker_with_state.checker_id,
                        )
                    )
                    break
        return IdleCheckResult(verdicts=verdicts)

    @override
    async def post_process(self, result: IdleCheckResult) -> None:
        pass

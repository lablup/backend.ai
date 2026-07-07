from __future__ import annotations

from typing import override

from ai.backend.common.types import SessionId
from ai.backend.manager.sokovan.idle_check.types import IdleCheckReconcileInfo, IdleCheckResult
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler


class IdleCheckReconcileHandler(ReconcilerHandler[IdleCheckReconcileInfo, IdleCheckResult]):
    """Turns prepared checks into idle verdicts; performs no external I/O."""

    @override
    async def execute(self, reconcile_info: IdleCheckReconcileInfo) -> IdleCheckResult:
        idle_session_ids: list[SessionId] = []
        for target in reconcile_info.targets:
            # First idle verdict in resolved order wins; at most one termination per session.
            for prepared_checker in target.checkers:
                if prepared_checker.check_idle(target.session_id):
                    idle_session_ids.append(target.session_id)
                    break
        return IdleCheckResult(idle_session_ids=idle_session_ids)

    @override
    async def post_process(self, result: IdleCheckResult) -> None:
        pass

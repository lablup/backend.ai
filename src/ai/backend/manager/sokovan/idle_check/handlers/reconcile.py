from __future__ import annotations

from typing import override

from ai.backend.manager.sokovan.idle_check.types import IdleCheckReconcileInfo, IdleCheckResult
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler


class IdleCheckReconcileHandler(ReconcilerHandler[IdleCheckReconcileInfo, IdleCheckResult]):
    @override
    async def execute(self, reconcile_info: IdleCheckReconcileInfo) -> IdleCheckResult:
        # Placeholder: idle judgment lands in the checker-logic stories.
        return IdleCheckResult()

    @override
    async def post_process(self, result: IdleCheckResult) -> None:
        pass

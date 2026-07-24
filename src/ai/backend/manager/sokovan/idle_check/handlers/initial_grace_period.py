from __future__ import annotations

from datetime import timedelta
from typing import override

from ai.backend.manager.sokovan.idle_check.initial_grace_period.types import (
    IdleCheckInitialGracePeriodReconcileInfo,
    IdleCheckInitialGracePeriodResult,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler


class IdleCheckInitialGracePeriodHandler(
    ReconcilerHandler[IdleCheckInitialGracePeriodReconcileInfo, IdleCheckInitialGracePeriodResult]
):
    @override
    async def execute(
        self,
        reconcile_info: IdleCheckInitialGracePeriodReconcileInfo,
    ) -> IdleCheckInitialGracePeriodResult:
        now = reconcile_info.batch.now
        pairs_to_ready = []
        for check in reconcile_info.batch.checks:
            grace_period = timedelta(seconds=check.initial_grace_period_seconds)
            grace_period_end = check.grace_started_at + grace_period
            if grace_period_end <= now:
                pairs_to_ready.append(check.pair)
        return IdleCheckInitialGracePeriodResult(pairs_to_ready=pairs_to_ready)

    @override
    async def post_process(self, result: IdleCheckInitialGracePeriodResult) -> None:
        pass

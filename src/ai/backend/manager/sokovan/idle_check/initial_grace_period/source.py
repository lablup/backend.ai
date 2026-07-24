from __future__ import annotations

from typing import override

from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.sokovan.idle_check.initial_grace_period.types import (
    IdleCheckInitialGracePeriodReconcileInfo,
)
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckCategory,
    IdleCheckTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerSource


class IdleCheckInitialGracePeriodSource(
    ReconcilerSource[
        IdleCheckInitialGracePeriodReconcileInfo,
        IdleCheckCategory,
        IdleCheckTargetStatuses,
    ]
):
    _repository: IdleCheckerRepository

    def __init__(self, repository: IdleCheckerRepository) -> None:
        self._repository = repository

    @override
    async def fetch_reconcile_info(
        self,
        category: IdleCheckCategory,
        target_statuses: IdleCheckTargetStatuses,
    ) -> IdleCheckInitialGracePeriodReconcileInfo:
        batch = await self._repository.fetch_initial_grace_period_checks(
            target_statuses.session_statuses
        )
        return IdleCheckInitialGracePeriodReconcileInfo(batch=batch)

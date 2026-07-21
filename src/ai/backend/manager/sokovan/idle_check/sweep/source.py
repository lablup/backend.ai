"""Source of the expiry-sweep stage: stored judgments whose deadline has passed."""

from __future__ import annotations

from typing import override

from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.sokovan.idle_check.sweep.types import IdleCheckSweepReconcileInfo
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckCategory,
    IdleCheckTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerSource


class IdleCheckSweepSource(
    ReconcilerSource[IdleCheckSweepReconcileInfo, IdleCheckCategory, IdleCheckTargetStatuses]
):
    _repository: IdleCheckerRepository

    def __init__(self, repository: IdleCheckerRepository) -> None:
        self._repository = repository

    @override
    async def fetch_reconcile_info(
        self,
        category: IdleCheckCategory,
        target_statuses: IdleCheckTargetStatuses,
    ) -> IdleCheckSweepReconcileInfo:
        batch = await self._repository.fetch_expired_idle_checks(target_statuses.session_statuses)
        return IdleCheckSweepReconcileInfo(batch=batch)

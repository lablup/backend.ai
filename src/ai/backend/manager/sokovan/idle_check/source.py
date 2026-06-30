from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckCategory,
    IdleCheckReconcileInfo,
    IdleCheckTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerSource


class IdleCheckSource(
    ReconcilerSource[IdleCheckReconcileInfo, IdleCheckCategory, IdleCheckTargetStatuses]
):
    _repository: IdleCheckerRepository

    def __init__(self, repository: IdleCheckerRepository) -> None:
        self._repository = repository

    @override
    async def fetch_reconcile_info(
        self,
        category: IdleCheckCategory,
        target_statuses: IdleCheckTargetStatuses,
    ) -> IdleCheckReconcileInfo:
        batch = await self._repository.fetch_idle_check_batch(target_statuses.session_statuses)
        return IdleCheckReconcileInfo(batch=batch, current_time=datetime.now(UTC))

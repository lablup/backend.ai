from __future__ import annotations

from typing import override

from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.sokovan.idle_check.assignment_sync.types import (
    IdleCheckAssignmentSyncReconcileInfo,
)
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckCategory,
    IdleCheckTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerSource


class IdleCheckAssignmentSyncSource(
    ReconcilerSource[
        IdleCheckAssignmentSyncReconcileInfo,
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
    ) -> IdleCheckAssignmentSyncReconcileInfo:
        assignments = await self._repository.fetch_session_idle_check_assignments(
            target_statuses.session_statuses
        )
        return IdleCheckAssignmentSyncReconcileInfo(
            desired_pairs=assignments.desired_pairs,
            current_pairs=assignments.current_pairs,
            current_time=assignments.now,
        )

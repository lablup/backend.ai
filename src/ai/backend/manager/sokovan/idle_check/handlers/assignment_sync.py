from __future__ import annotations

from typing import override

from ai.backend.manager.sokovan.idle_check.assignment_sync.types import (
    IdleCheckAssignmentSyncReconcileInfo,
    IdleCheckAssignmentSyncResult,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerHandler


class IdleCheckAssignmentSyncHandler(
    ReconcilerHandler[IdleCheckAssignmentSyncReconcileInfo, IdleCheckAssignmentSyncResult]
):
    @override
    async def execute(
        self, reconcile_info: IdleCheckAssignmentSyncReconcileInfo
    ) -> IdleCheckAssignmentSyncResult:
        desired = set(reconcile_info.desired_pairs)
        current = set(reconcile_info.current_pairs)
        return IdleCheckAssignmentSyncResult(
            pairs_to_create=list(desired - current),
            pairs_to_delete=list(current - desired),
            current_time=reconcile_info.current_time,
        )

    @override
    async def post_process(self, result: IdleCheckAssignmentSyncResult) -> None:
        pass

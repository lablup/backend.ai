from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckCategory,
    IdleCheckReconcileInfo,
    IdleCheckTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerSource


class IdleCheckSource(
    ReconcilerSource[IdleCheckReconcileInfo, IdleCheckCategory, IdleCheckTargetStatuses]
):
    @override
    async def fetch_reconcile_info(
        self,
        category: IdleCheckCategory,
        target_statuses: IdleCheckTargetStatuses,
    ) -> IdleCheckReconcileInfo:
        # Placeholder: the per-resource-group session/checker fetch lands in a follow-up.
        return IdleCheckReconcileInfo(session_ids=(), current_time=datetime.now(UTC))

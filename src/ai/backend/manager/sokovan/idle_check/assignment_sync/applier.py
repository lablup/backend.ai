from __future__ import annotations

from typing import override

from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.sokovan.idle_check.assignment_sync.types import (
    IdleCheckAssignmentSyncResult,
)
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckCategory,
    IdleCheckKind,
    IdleCheckTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerApplier, ReconcilerApplyInput

_IdleCheckAssignmentSyncApplyInput = ReconcilerApplyInput[
    IdleCheckAssignmentSyncResult,
    IdleCheckCategory,
    IdleCheckKind,
    IdleCheckTargetStatuses,
    SessionStatus,
]


class IdleCheckAssignmentSyncApplier(
    ReconcilerApplier[
        IdleCheckAssignmentSyncResult,
        IdleCheckCategory,
        IdleCheckKind,
        IdleCheckTargetStatuses,
        SessionStatus,
    ]
):
    _repository: IdleCheckerRepository

    def __init__(self, repository: IdleCheckerRepository) -> None:
        self._repository = repository

    @override
    async def apply(self, apply_input: _IdleCheckAssignmentSyncApplyInput) -> None:
        result = apply_input.result
        if len(result.pairs_to_create) == 0 and len(result.pairs_to_delete) == 0:
            return
        await self._repository.sync_session_idle_check_assignments(
            result.pairs_to_create,
            result.pairs_to_delete,
            result.current_time,
        )

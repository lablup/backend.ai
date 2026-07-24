from __future__ import annotations

from typing import override

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.sokovan.idle_check.initial_grace.types import (
    IdleCheckInitialGraceResult,
)
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckCategory,
    IdleCheckKind,
    IdleCheckTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerApplier, ReconcilerApplyInput

_IdleCheckInitialGraceApplyInput = ReconcilerApplyInput[
    IdleCheckInitialGraceResult,
    IdleCheckCategory,
    IdleCheckKind,
    IdleCheckTargetStatuses,
    SessionStatus,
]


class IdleCheckInitialGraceApplier(
    ReconcilerApplier[
        IdleCheckInitialGraceResult,
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
    async def apply(self, apply_input: _IdleCheckInitialGraceApplyInput) -> None:
        pairs = apply_input.result.pairs_to_ready
        if not pairs:
            return
        await self._repository.batch_update_session_idle_check_phase(
            pairs,
            from_phase=IdleCheckPhase.NOT_CHECKED,
            to_phase=IdleCheckPhase.READY_TO_CHECK,
        )

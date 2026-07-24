from __future__ import annotations

from collections import defaultdict
from typing import override

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.repositories.idle_checker.repository import IdleCheckerRepository
from ai.backend.manager.repositories.idle_checker.types import IdleJudgmentData
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckCategory,
    IdleCheckKind,
    IdleCheckResult,
    IdleCheckTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerApplier, ReconcilerApplyInput

_IdleCheckApplyInput = ReconcilerApplyInput[
    IdleCheckResult,
    IdleCheckCategory,
    IdleCheckKind,
    IdleCheckTargetStatuses,
    SessionStatus,
]


class IdleCheckApplier(
    ReconcilerApplier[
        IdleCheckResult,
        IdleCheckCategory,
        IdleCheckKind,
        IdleCheckTargetStatuses,
        SessionStatus,
    ]
):
    """Persist handler-judged phases onto existing session_idle_checks rows verbatim."""

    _repository: IdleCheckerRepository

    def __init__(self, repository: IdleCheckerRepository) -> None:
        self._repository = repository

    @override
    async def apply(self, apply_input: _IdleCheckApplyInput) -> None:
        judgments = apply_input.result.judgments
        if not judgments:
            return
        by_status: defaultdict[IdleCheckPhase, list[IdleJudgmentData]] = defaultdict(list)
        for judgment in judgments:
            by_status[judgment.status].append(judgment)
        await self._repository.batch_apply_session_idle_check_judgments(
            idle_expired=by_status[IdleCheckPhase.IDLE_EXPIRED],
            idle=by_status[IdleCheckPhase.IDLE],
            active=by_status[IdleCheckPhase.ACTIVE],
        )

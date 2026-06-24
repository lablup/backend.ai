from __future__ import annotations

from typing import override

from ai.backend.manager.data.session.types import SessionStatus
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
    @override
    async def apply(self, apply_input: _IdleCheckApplyInput) -> None:
        # Placeholder: marking result.idle_session_ids TERMINATING via
        # SchedulingController.mark_sessions_for_termination lands in a follow-up.
        pass

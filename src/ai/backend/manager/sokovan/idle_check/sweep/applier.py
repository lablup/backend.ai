"""No-op applier for the handler-driven idle-check sweep."""

from __future__ import annotations

from typing import override

from ai.backend.manager.data.session.types import SessionStatus
from ai.backend.manager.sokovan.idle_check.sweep.types import IdleCheckSweepResult
from ai.backend.manager.sokovan.idle_check.types import (
    IdleCheckCategory,
    IdleCheckKind,
    IdleCheckTargetStatuses,
)
from ai.backend.manager.sokovan.reconciler.base import ReconcilerApplier, ReconcilerApplyInput

_IdleCheckSweepApplyInput = ReconcilerApplyInput[
    IdleCheckSweepResult,
    IdleCheckCategory,
    IdleCheckKind,
    IdleCheckTargetStatuses,
    SessionStatus,
]


class IdleCheckSweepApplier(
    ReconcilerApplier[
        IdleCheckSweepResult,
        IdleCheckCategory,
        IdleCheckKind,
        IdleCheckTargetStatuses,
        SessionStatus,
    ]
):
    @override
    async def apply(self, apply_input: _IdleCheckSweepApplyInput) -> None:
        pass

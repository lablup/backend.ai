"""Idle checker contract driven once per checker type by the reconcile handler."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerDefinitionData


@dataclass(frozen=True)
class IdleCheckerContext:
    """Shared execution context for every checker in one reconcile tick."""

    current_time: datetime


@dataclass(frozen=True)
class CheckerAssignment:
    """One checker definition and the sessions it must judge this tick."""

    definition: IdleCheckerDefinitionData
    sessions: Sequence[IdleCheckSession]


@dataclass(frozen=True)
class IdleActivityDecision:
    """One checker's activity decision before lifecycle phase resolution."""

    session_id: SessionId
    checker_id: IdleCheckerID
    is_active: bool
    expire_at: datetime
    message: str


class IdleChecker(ABC):
    """Per-``CheckerType`` behavior with constructor-injected I/O clients."""

    @abstractmethod
    async def judge(
        self,
        assignments: Sequence[CheckerAssignment],
        *,
        context: IdleCheckerContext,
    ) -> Sequence[IdleActivityDecision]:
        """Evaluate every assignment of this type in one batched call.

        Implementations may batch external I/O but must not retain per-call state.
        The reconcile handler converts decisions into persisted lifecycle judgments.
        """
        raise NotImplementedError

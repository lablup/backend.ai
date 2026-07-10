"""Idle checker contract: prepare (batched I/O) + judge (pure), driven by the reconcile handler."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerDefinitionData


@dataclass(frozen=True)
class CheckerAssignment:
    """One checker definition and the sessions it must judge this tick."""

    definition: IdleCheckerDefinitionData
    sessions: Sequence[IdleCheckSession]


@dataclass(frozen=True)
class IdleJudgment:
    """One session's judgment from one checker definition."""

    session_id: SessionId
    is_idle: bool
    message: str


class IdleChecker[StateT](ABC):
    """Per-``CheckerType`` behavior; ``StateT`` is one session's judgment material.

    Concrete checkers receive the I/O clients ``prepare`` needs via their constructors.
    """

    @abstractmethod
    async def prepare(
        self,
        assignments: Sequence[CheckerAssignment],
    ) -> Mapping[IdleCheckerID, Mapping[SessionId, StateT]]:
        """Called once per tick with every definition of this type.

        Batch the I/O across all assignments (session ids key the Valkey/DB reads) and
        bake everything ``judge`` needs into per-session states.
        """
        raise NotImplementedError

    @abstractmethod
    def judge(self, session_states: Mapping[SessionId, StateT]) -> Sequence[IdleJudgment]:
        """Judge one definition's sessions from prepared states alone; no I/O."""
        raise NotImplementedError

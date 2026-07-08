"""Idle checker contract: prepare (I/O, Source phase) + check_idle (pure)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.repositories.idle_checker.types import IdleCheckerDefinitionData


@dataclass(frozen=True)
class IdleCheckContext:
    """I/O clients used by ``prepare``; filled in by the checker-logic stories."""


class IdleCheckerState:
    """Marker for the state a checker prepares; each checker defines its own shape."""


@dataclass(frozen=True)
class PrepareRequest:
    """One checker definition and the sessions it must judge this tick."""

    definition: IdleCheckerDefinitionData
    sessions: Sequence[IdleCheckSession]


class IdleChecker(ABC):
    """Stateless per-``CheckerType`` judgment behavior."""

    @abstractmethod
    async def prepare(
        self,
        context: IdleCheckContext,
        requests: Sequence[PrepareRequest],
    ) -> Mapping[IdleCheckerID, IdleCheckerState]:
        """Called once per tick with every definition of this type.

        Batch the I/O across all requests and return one state per definition;
        capture everything check_idle needs into the states here.
        """
        raise NotImplementedError

    @abstractmethod
    def check_idle(self, session_id: SessionId, state: IdleCheckerState) -> bool:
        """Judge one session from prepared state alone; True means idle."""
        raise NotImplementedError

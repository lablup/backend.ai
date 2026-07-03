"""Repository result types for the idle-check reconciler batch."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.idle_checker.types import CheckerType, IdleCheckerSpec
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.manager.data.idle_checker.types import IdleCheckSession, ScopeRef


@dataclass(frozen=True)
class IdleCheckerDefinitionData:
    """An idle checker definition with its typed, loaded spec."""

    checker_id: IdleCheckerID
    checker_type: CheckerType
    spec: IdleCheckerSpec


@dataclass(frozen=True)
class BoundCheckerData:
    """A checker applied through a concrete scope binding.

    ``binding_created_at`` is the stable tiebreak within the same scope.
    """

    scope: ScopeRef
    binding_created_at: datetime
    checker: IdleCheckerDefinitionData


@dataclass(frozen=True)
class IdleCheckTargetData:
    """One session and the checkers applicable to it in this batch."""

    session: IdleCheckSession
    checkers: Sequence[BoundCheckerData]


@dataclass(frozen=True)
class IdleCheckBatchData:
    """Handler-oriented idle-check input for one reconciler tick."""

    targets: Sequence[IdleCheckTargetData]

"""Repository result types for the idle-check reconciler batch."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.idle_checker.types import CheckerType, IdleCheckerSpec
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.data.permission.id import ScopeId


@dataclass(frozen=True)
class IdleCheckerDefinitionData:
    """An idle checker definition with its typed, loaded spec."""

    checker_id: IdleCheckerID
    checker_type: CheckerType
    target_session_types: frozenset[SessionTypes]
    spec: IdleCheckerSpec


@dataclass(frozen=True)
class BoundCheckerData:
    """A checker applied through a concrete scope binding.

    ``binding_created_at`` is the stable tiebreak within the same scope.
    """

    scope: ScopeId
    binding_created_at: datetime
    checker: IdleCheckerDefinitionData


@dataclass(frozen=True)
class IdleCheckSessionData:
    """Session data plus scope refs needed to attach bound idle checkers."""

    session: IdleCheckSession
    session_type: SessionTypes
    scopes: Sequence[ScopeId]


@dataclass(frozen=True)
class IdleCheckTargetData:
    """One session and the checkers applicable to it in this batch."""

    session: IdleCheckSession
    checkers: Sequence[BoundCheckerData]


@dataclass(frozen=True)
class IdleCheckBatchData:
    """Handler-oriented idle-check input for one reconciler tick."""

    targets: Sequence[IdleCheckTargetData]


@dataclass(frozen=True)
class ExpiredIdleCheckData:
    """One stored judgment whose deadline has passed, kept per checker as its own reason."""

    session_id: SessionId
    checker_id: IdleCheckerID
    expire_at: datetime
    last_status: str
    last_message: str


@dataclass(frozen=True)
class ExpiredIdleCheckBatchData:
    """Sweep input for one reconciler tick.

    ``now`` is the DB time read in the same transaction as the fetch, so every
    returned check satisfies ``expire_at <= now``.
    """

    checks: Sequence[ExpiredIdleCheckData]
    now: datetime

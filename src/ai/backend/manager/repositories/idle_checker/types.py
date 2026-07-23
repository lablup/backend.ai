"""Repository result types for the idle-check reconciler batch."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from ai.backend.common.data.idle_checker.types import CheckerType, IdleCheckerSpec, IdleCheckPhase
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession


@dataclass(frozen=True)
class IdleCheckerDefinitionData:
    """An idle checker definition with its typed, loaded spec."""

    checker_id: IdleCheckerID
    checker_type: CheckerType
    target_session_types: frozenset[SessionTypes]
    spec: IdleCheckerSpec


@dataclass(frozen=True)
class IdleCheckAssignmentData:
    """One existing session idle-check row with data needed for judgment."""

    session: IdleCheckSession
    checker: IdleCheckerDefinitionData


@dataclass(frozen=True)
class IdleCheckBatchData:
    """Handler-oriented idle-check input for one reconciler tick."""

    assignments: Sequence[IdleCheckAssignmentData]


@dataclass(frozen=True)
class SessionIdleCheckPair:
    session_id: SessionId
    checker_id: IdleCheckerID


@dataclass(frozen=True)
class InitialGracePeriodCheckData:
    pair: SessionIdleCheckPair
    initial_grace_seconds: int
    grace_started_at: datetime


@dataclass(frozen=True)
class InitialGracePeriodBatchData:
    checks: Sequence[InitialGracePeriodCheckData]
    now: datetime


@dataclass(frozen=True)
class SessionIdleCheckAssignmentData:
    # Pairs that should exist, derived from enabled checker scope bindings.
    desired_pairs: Sequence[SessionIdleCheckPair]
    # Existing pairs for sessions in the target statuses, excluding terminal sessions.
    current_pairs: Sequence[SessionIdleCheckPair]
    now: datetime


@dataclass(frozen=True)
class ExpiredIdleCheckData:
    """One stored judgment whose deadline has passed, kept per checker as its own reason."""

    session_id: SessionId
    checker_id: IdleCheckerID
    expire_at: datetime
    last_status: IdleCheckPhase
    last_message: str


@dataclass(frozen=True)
class ExpiredIdleCheckBatchData:
    """Idle checks expired as of the DB timestamp.
    `now` is the same timestamp passed to the reconciler.
    """

    checks: Sequence[ExpiredIdleCheckData]
    now: datetime

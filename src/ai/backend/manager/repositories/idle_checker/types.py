"""Repository result types for idle checkers."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.idle_checker.types import CheckerType, IdleCheckerSpec, IdleCheckPhase
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.idle_checker.row import IdleCheckerBindingRow
from ai.backend.manager.models.scopes import ExistenceCheck, SearchScope


@dataclass(frozen=True)
class IdleCheckerAssignmentSearchScope(SearchScope):
    """Idle checker bindings attached to one ``(scope_type, scope_id)`` pair.

    One scope = one item of a scoped binding query; the repository layer
    combines multiple scopes with ``OR`` to realize the ``IdleCheckerAssignmentScope``
    union semantics.

    ``existence_checks`` is empty by ``SearchableActionTarget`` convention —
    RBAC validation already gates scope reachability.
    """

    scope_type: ScopeType
    scope_id: uuid.UUID

    @override
    def to_condition(self) -> QueryCondition:
        scope_type = self.scope_type
        scope_id = self.scope_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                IdleCheckerBindingRow.scope_type == scope_type,
                IdleCheckerBindingRow.scope_id == scope_id,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()


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
    now: datetime


@dataclass(frozen=True)
class SessionIdleCheckPair:
    session_id: SessionId
    checker_id: IdleCheckerID


@dataclass(frozen=True)
class IdleJudgmentData:
    """One session's judgment from one checker, persisted onto its session_idle_checks row."""

    session_id: SessionId
    checker_id: IdleCheckerID
    status: IdleCheckPhase
    expire_at: datetime
    message: str


@dataclass(frozen=True)
class InitialGracePeriodCheckData:
    pair: SessionIdleCheckPair
    initial_grace_period_seconds: int
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
    """One stored IDLE_EXPIRED judgment, kept per checker as its own reason."""

    session_id: SessionId
    checker_id: IdleCheckerID
    expire_at: datetime
    last_status: IdleCheckPhase
    last_message: str


@dataclass(frozen=True)
class ExpiredIdleCheckBatchData:
    """Stored IDLE_EXPIRED judgments and the DB timestamp for the reconciler."""

    checks: Sequence[ExpiredIdleCheckData]
    now: datetime

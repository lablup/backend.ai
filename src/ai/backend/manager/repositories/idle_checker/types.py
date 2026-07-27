"""Repository result types for idle checkers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import (
    EntityRef,
    ScopeRef,
)
from ai.backend.common.data.entity.types import (
    EntityType as VirtualScopeEntityType,
)
from ai.backend.common.data.idle_checker.types import CheckerType, IdleCheckerSpec, IdleCheckPhase
from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.common.exception import UserNotFound
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.identifier.user import UserID
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckSession
from ai.backend.manager.errors.idle_checker import IdleCheckerOwnerScopeNotSupported
from ai.backend.manager.errors.resource import ProjectNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.scopes import ExistenceCheck, SearchScope
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.repositories.ops.rbac.provider import ScopeMember


@dataclass(frozen=True)
class IdleCheckerSearchScope(SearchScope):
    scope: ScopeRef

    @override
    def to_condition(self) -> QueryCondition:
        try:
            scope_type = ScopeType(self.scope.scope_type)
        except ValueError as e:
            raise IdleCheckerOwnerScopeNotSupported(str(self.scope.scope_type)) from e
        if scope_type not in (ScopeType.USER, ScopeType.PROJECT):
            raise IdleCheckerOwnerScopeNotSupported(scope_type.value)
        scope_id = str(self.scope.scope_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                AssociationScopesEntitiesRow.scope_type == scope_type,
                AssociationScopesEntitiesRow.scope_id == scope_id,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        if self.scope.scope_type == ScopeType.USER.value:
            return [
                ExistenceCheck(
                    column=UserRow.uuid,
                    value=self.scope.scope_id,
                    error=UserNotFound(extra_data={"user_id": str(self.scope.scope_id)}),
                )
            ]
        if self.scope.scope_type == ScopeType.PROJECT.value:
            return [
                ExistenceCheck(
                    column=GroupRow.id,
                    value=self.scope.scope_id,
                    error=ProjectNotFound(str(self.scope.scope_id)),
                )
            ]
        raise IdleCheckerOwnerScopeNotSupported(str(self.scope.scope_type))


@dataclass(frozen=True)
class IdleCheckerScopeMember(ScopeMember):
    checker_id: IdleCheckerID

    @override
    def entity_ref(self) -> EntityRef:
        return EntityRef(
            entity_type=VirtualScopeEntityType(EntityType.IDLE_CHECKER.value),
            entity_id=self.checker_id,
        )

    @override
    def assign_role_on(self) -> UserID | None:
        return None


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

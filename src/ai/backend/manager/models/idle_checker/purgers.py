from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.idle_checker.row import (
    IdleCheckerBindingRow,
    IdleCheckerRow,
    SessionIdleCheckRow,
)
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.relation import RelationPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class IdleCheckerPurger(EntityPurger[IdleCheckerRow, IdleCheckerData]):
    """Purger for removing an idle checker definition from the catalog.

    Purge-shaped: the table carries no lifecycle column, so removing one has always
    been the row leaving the table. Its bindings and session rows follow through
    ``ON DELETE CASCADE``.
    """

    checker_id: IdleCheckerID

    @override
    def entity_id(self) -> IdleCheckerID:
        return self.checker_id

    @override
    def row_class(self) -> type[IdleCheckerRow]:
        return IdleCheckerRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return IdleCheckerRow.id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: IdleCheckerRow) -> IdleCheckerData:
        return row.to_data()


@dataclass
class IdleCheckerAssignmentPurger(
    RelationPurger[EntityIdentifier, IdleCheckerID, IdleCheckerBindingRow]
):
    """Unlinks a scope from an idle checker."""

    @override
    def row_class(self) -> type[IdleCheckerBindingRow]:
        return IdleCheckerBindingRow

    @override
    def conditions(
        self, scope: EntityIdentifier, target: IdleCheckerID
    ) -> Sequence[QueryCondition]:
        return (
            lambda: IdleCheckerBindingRow.scope_type == scope.entity_type(),
            lambda: IdleCheckerBindingRow.scope_id == scope,
            lambda: IdleCheckerBindingRow.idle_checker_id == target,
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()


@dataclass
class SessionIdleCheckUnlink(RelationPurger[SessionID, IdleCheckerID, SessionIdleCheckRow]):
    """Unlinks a session from a checker that no longer applies to it.

    A pair already expired, or one an operator triggered by hand, is left alone: the
    sweep removes what the assignment no longer covers, not what someone decided.
    """

    @override
    def row_class(self) -> type[SessionIdleCheckRow]:
        return SessionIdleCheckRow

    @override
    def conditions(self, scope: SessionID, target: IdleCheckerID) -> Sequence[QueryCondition]:
        return (
            lambda: SessionIdleCheckRow.session_id == scope,
            lambda: SessionIdleCheckRow.idle_checker_id == target,
            lambda: SessionIdleCheckRow.last_status != IdleCheckPhase.IDLE_EXPIRED,
            lambda: sa.not_(SessionIdleCheckRow.is_manual),
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

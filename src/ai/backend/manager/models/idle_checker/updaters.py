from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.idle_checker.types import IdleCheckerSpec, IdleCheckPhase
from ai.backend.common.types import SessionId, SessionTypes
from ai.backend.manager.data.idle_checker.types import (
    IdleCheckerData,
    IdleJudgmentData,
    SessionIdleCheckData,
)
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.idle_checker.conditions import SessionIdleCheckConditions
from ai.backend.manager.models.idle_checker.row import (
    IdleCheckerBindingRow,
    IdleCheckerRow,
    SessionIdleCheckRow,
)
from ai.backend.manager.models.specs.relation import RelationLifecycleUpdater
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataBatchUpdater, DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class IdleCheckerUpdater(DataUpdater[IdleCheckerRow, IdleCheckerData]):
    """Retune one stored idle checker definition.

    ``checker_type`` is not a field: the column is computed from ``spec`` by the
    database.
    """

    checker_id: IdleCheckerID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    target_session_types: OptionalState[list[SessionTypes]] = field(
        default_factory=OptionalState[list[SessionTypes]].nop
    )
    initial_grace_period_seconds: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    spec: OptionalState[IdleCheckerSpec] = field(default_factory=OptionalState[IdleCheckerSpec].nop)

    @property
    @override
    def row_class(self) -> type[IdleCheckerRow]:
        return IdleCheckerRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return IdleCheckerRow.id

    @override
    def target_id_value(self) -> IdleCheckerID:
        return self.checker_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.target_session_types.update_dict(to_update, "target_session_types")
        self.initial_grace_period_seconds.update_dict(to_update, "initial_grace_period_seconds")
        self.spec.update_dict(to_update, "spec")
        return to_update

    @override
    def to_data(self, row: IdleCheckerRow) -> IdleCheckerData:
        return row.to_data()


class IdleCheckerAssignmentSwitch(
    RelationLifecycleUpdater[EntityIdentifier, IdleCheckerID, IdleCheckerBindingRow]
):
    """Names the pair's row; the two subclasses each write one constant."""

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


class IdleCheckerAssignmentDisabler(IdleCheckerAssignmentSwitch):
    """Switches the binding off. Handed to ``delete_relation``."""

    @override
    def build_values(self) -> dict[str, Any]:
        return {"enabled": False}


class IdleCheckerAssignmentEnabler(IdleCheckerAssignmentSwitch):
    """Switches the binding back on. Handed to ``restore_relation``."""

    @override
    def build_values(self) -> dict[str, Any]:
        return {"enabled": True}


@dataclass
class SessionIdleCheckPhaseBatchUpdater(
    DataBatchUpdater[SessionIdleCheckRow, SessionIdleCheckData]
):
    """Move the named pairs from one phase to another."""

    pairs: Sequence[tuple[SessionId, IdleCheckerID]]
    from_phase: IdleCheckPhase
    to_phase: IdleCheckPhase

    @property
    @override
    def row_class(self) -> type[SessionIdleCheckRow]:
        return SessionIdleCheckRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [
            SessionIdleCheckConditions.by_pairs(self.pairs),
            SessionIdleCheckConditions.by_status_equals(self.from_phase),
        ]

    @override
    def build_values(self) -> dict[str, Any]:
        return {"last_status": self.to_phase}

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: SessionIdleCheckRow) -> SessionIdleCheckData:
        return row.to_data()


@dataclass
class SessionIdleCheckJudgmentBatchUpdater(
    DataBatchUpdater[SessionIdleCheckRow, SessionIdleCheckData]
):
    """Write each pair's judgment, leaving the pairs no longer being checked alone."""

    judgments: Sequence[IdleJudgmentData]

    @property
    @override
    def row_class(self) -> type[SessionIdleCheckRow]:
        return SessionIdleCheckRow

    @override
    def conditions(self) -> list[QueryCondition]:
        return [
            SessionIdleCheckConditions.by_pairs([
                (judgment.session_id, judgment.checker_id) for judgment in self.judgments
            ]),
            SessionIdleCheckConditions.by_statuses((
                IdleCheckPhase.READY_TO_CHECK,
                IdleCheckPhase.ACTIVE,
                IdleCheckPhase.IDLE,
            )),
        ]

    def _per_pair(self, value_of: Callable[[IdleJudgmentData], Any]) -> sa.Case[Any]:
        return sa.case(*[
            (
                sa.and_(
                    SessionIdleCheckRow.session_id == judgment.session_id,
                    SessionIdleCheckRow.idle_checker_id == judgment.checker_id,
                ),
                value_of(judgment),
            )
            for judgment in self.judgments
        ])

    @override
    def build_values(self) -> dict[str, Any]:
        return {
            "last_status": self._per_pair(lambda judgment: judgment.status),
            "expire_at": self._per_pair(lambda judgment: judgment.expire_at),
            "last_message": self._per_pair(lambda judgment: judgment.message),
        }

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def to_data(self, row: SessionIdleCheckRow) -> SessionIdleCheckData:
        return row.to_data()

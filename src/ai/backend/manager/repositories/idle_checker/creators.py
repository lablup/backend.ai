from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.idle_checker.types import IdleCheckerSpec, IdleCheckPhase
from ai.backend.common.data.permission.types import ScopeType
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.types import SessionTypes
from ai.backend.manager.errors.idle_checker import (
    IdleCheckerAssignmentAlreadyExists,
    IdleCheckerNotFound,
)
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.models.idle_checker.row import (
    IdleCheckerBindingRow,
    IdleCheckerRow,
    SessionIdleCheckRow,
)
from ai.backend.manager.repositories.base import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck
from ai.backend.manager.repositories.idle_checker.types import SessionIdleCheckPair


@dataclass
class IdleCheckerCreatorSpec(CreatorSpec[IdleCheckerRow]):
    name: str
    description: str | None
    target_session_types: list[SessionTypes]
    initial_grace_period_seconds: int
    spec: IdleCheckerSpec

    @override
    def build_row(self) -> IdleCheckerRow:
        return IdleCheckerRow(
            name=self.name,
            description=self.description,
            target_session_types=self.target_session_types,
            initial_grace_period_seconds=self.initial_grace_period_seconds,
            spec=self.spec,
        )


@dataclass
class IdleCheckerAssignmentCreatorSpec(CreatorSpec[IdleCheckerBindingRow]):
    scope_type: ScopeType
    scope_id: uuid.UUID
    idle_checker_id: IdleCheckerID
    enabled: bool

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=IdleCheckerAssignmentAlreadyExists(
                    f"Idle checker {self.idle_checker_id} is already bound to "
                    f"{self.scope_type.value}:{self.scope_id}"
                ),
                constraint_name="uq_idle_checker_bindings_checker_scope",
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=IdleCheckerNotFound(str(self.idle_checker_id)),
                constraint_name="fk_idle_checker_bindings_idle_checker_id",
            ),
        )

    @override
    def build_row(self) -> IdleCheckerBindingRow:
        return IdleCheckerBindingRow(
            scope_type=self.scope_type,
            scope_id=self.scope_id,
            idle_checker_id=self.idle_checker_id,
            enabled=self.enabled,
        )


@dataclass
class SessionIdleCheckCreatorSpec(CreatorSpec[SessionIdleCheckRow]):
    pair: SessionIdleCheckPair

    @override
    def build_row(self) -> SessionIdleCheckRow:
        return SessionIdleCheckRow(
            session_id=self.pair.session_id,
            idle_checker_id=self.pair.checker_id,
            expire_at=None,
            last_status=IdleCheckPhase.NOT_CHECKED,
            last_message="Not checked yet.",
        )

"""Upsert specs of the idle checkers and session idle checks tables."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.idle_checker import IdleCheckerID
from ai.backend.common.data.entity.session import SessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.idle_checker.types import IdleCheckerSpec, IdleCheckPhase
from ai.backend.common.types import SessionTypes
from ai.backend.manager.data.idle_checker.types import IdleCheckerData
from ai.backend.manager.errors.idle_checker import IdleCheckerNotFound
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.models.idle_checker.row import IdleCheckerRow, SessionIdleCheckRow
from ai.backend.manager.models.idle_checker.searchable_fields import (
    IdleCheckerSearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInGlobal
from ai.backend.manager.models.specs.relation import RelationUpserter
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter


@dataclass
class IdleCheckerUpserter(
    CreatedInGlobal[IdleCheckerRow], EntityUpserter[IdleCheckerRow, IdleCheckerData]
):
    """Write an idle checker under its stated id.

    Conflict key: id. An update rewrites every stated column.
    """

    id: IdleCheckerID
    name: str
    description: str | None
    target_session_types: list[SessionTypes]
    initial_grace_period_seconds: int
    spec: IdleCheckerSpec

    @override
    def entity_id(self, row: IdleCheckerRow) -> IdleCheckerID:
        return IdleCheckerID(row.id)

    @override
    def row_class(self) -> type[IdleCheckerRow]:
        return IdleCheckerRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, **self._stated_values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._stated_values(), "updated_at": sa.func.now()}

    def _stated_values(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "target_session_types": self.target_session_types,
            "initial_grace_period_seconds": self.initial_grace_period_seconds,
            "spec": self.spec,
        }

    @override
    def to_data(self, row: IdleCheckerRow) -> IdleCheckerData:
        return IdleCheckerSearchableFields.own.to_data(row)


@dataclass
class SessionIdleCheckExcluder(RelationUpserter[SessionID, IdleCheckerID, SessionIdleCheckRow]):
    """Put a pair in the excluded state, whether or not the checker reached it yet.

    An upsert rather than a switch: an operator excluding a session before the sweep
    has linked it still means the checker must leave it alone. The row is marked
    manual and stamped with the writer, so the sweep leaves it alone too.
    """

    user_id: UserID

    @override
    def row_class(self) -> type[SessionIdleCheckRow]:
        return SessionIdleCheckRow

    @override
    def index_elements(self) -> list[str]:
        return ["session_id", "idle_checker_id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_session_idle_checks_session_id",
                error=SessionNotFound("Session not found."),
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_session_idle_checks_idle_checker_id",
                error=IdleCheckerNotFound("Idle checker not found."),
            ),
        )

    def _values(self) -> dict[str, Any]:
        return {
            "last_status": IdleCheckPhase.EXCLUDED,
            "expire_at": None,
            "last_message": "Excluded from idle checks.",
            "is_manual": True,
            "manually_triggered_by": self.user_id,
        }

    @override
    def build_insert_values(self, scope: SessionID, target: IdleCheckerID) -> dict[str, Any]:
        return {"session_id": scope, "idle_checker_id": target, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        return self._values()


@dataclass
class SessionIdleCheckIncluder(SessionIdleCheckExcluder):
    """Put a pair back under the checker, restarting its checks from the grace period.

    The write stamps ``updated_at`` itself: the grace period counts from here, and an
    ON CONFLICT UPDATE does not run the column's ``onupdate``.
    """

    @override
    def _values(self) -> dict[str, Any]:
        return {
            "last_status": IdleCheckPhase.NOT_CHECKED,
            "expire_at": None,
            "last_message": "Not checked yet.",
            "is_manual": True,
            "manually_triggered_by": self.user_id,
            "updated_at": datetime.now(UTC),
        }

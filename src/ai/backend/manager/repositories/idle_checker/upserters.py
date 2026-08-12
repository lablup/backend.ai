from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, override

from ai.backend.common.data.idle_checker.types import IdleCheckPhase
from ai.backend.common.identifier.idle_checker import IdleCheckerID
from ai.backend.common.identifier.session import SessionID
from ai.backend.common.identifier.user import UserID
from ai.backend.manager.errors.idle_checker import IdleCheckerNotFound
from ai.backend.manager.errors.kernel import SessionNotFound
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.models.idle_checker.row import SessionIdleCheckRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.repositories.base import UpserterSpec


@dataclass
class SessionIdleCheckExcludeUpserterSpec(UpserterSpec[SessionIdleCheckRow]):
    """Mark a pair EXCLUDED, creating the row when assignment-sync has not yet.

    Records the managing writer: the row is marked manual and stamped with the
    requesting user, so assignment-sync leaves it alone.
    """

    session_id: SessionID
    checker_id: IdleCheckerID
    user_id: UserID

    @property
    @override
    def row_class(self) -> type[SessionIdleCheckRow]:
        return SessionIdleCheckRow

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=SessionNotFound(str(self.session_id)),
                constraint_name="fk_session_idle_checks_session_id",
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=IdleCheckerNotFound(str(self.checker_id)),
                constraint_name="fk_session_idle_checks_idle_checker_id",
            ),
        )

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "idle_checker_id": self.checker_id,
            "last_status": IdleCheckPhase.EXCLUDED,
            "expire_at": None,
            "last_message": "Excluded from idle checks.",
            "is_manual": True,
            "manually_triggered_by": self.user_id,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "last_status": IdleCheckPhase.EXCLUDED,
            "expire_at": None,
            "last_message": "Excluded from idle checks.",
            "is_manual": True,
            "manually_triggered_by": self.user_id,
            "updated_at": datetime.now(UTC),
        }


@dataclass
class SessionIdleCheckIncludeUpserterSpec(UpserterSpec[SessionIdleCheckRow]):
    """Reset a pair to NOT_CHECKED so its checks restart from the grace period.

    Records the managing writer: the row is marked manual and stamped with the
    requesting user, so assignment-sync leaves it alone.
    """

    session_id: SessionID
    checker_id: IdleCheckerID
    user_id: UserID

    @property
    @override
    def row_class(self) -> type[SessionIdleCheckRow]:
        return SessionIdleCheckRow

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=SessionNotFound(str(self.session_id)),
                constraint_name="fk_session_idle_checks_session_id",
            ),
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                error=IdleCheckerNotFound(str(self.checker_id)),
                constraint_name="fk_session_idle_checks_idle_checker_id",
            ),
        )

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "idle_checker_id": self.checker_id,
            "last_status": IdleCheckPhase.NOT_CHECKED,
            "expire_at": None,
            "last_message": "Not checked yet.",
            "is_manual": True,
            "manually_triggered_by": self.user_id,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "last_status": IdleCheckPhase.NOT_CHECKED,
            "expire_at": None,
            "last_message": "Not checked yet.",
            "is_manual": True,
            "manually_triggered_by": self.user_id,
            "updated_at": datetime.now(UTC),
        }

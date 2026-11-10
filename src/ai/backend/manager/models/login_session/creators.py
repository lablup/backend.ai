"""Insert specs for the login_sessions and login_history tables."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.login_history import LoginHistoryID
from ai.backend.common.data.entity.login_session import LoginSessionID
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.data.auth.login_session_types import (
    LoginAttemptResult,
    LoginHistoryData,
    LoginSessionData,
    LoginSessionStatus,
)
from ai.backend.manager.errors.repository import ForeignKeyViolationError
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.models.specs.creator import FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class LoginSessionCreator(FieldCreator[UserID, LoginSessionRow, LoginSessionData]):
    """Creator for one login session, written under the user who signed in."""

    session_token: str
    access_key: str
    status: LoginSessionStatus = LoginSessionStatus.ACTIVE

    @override
    def field_id(self, row: LoginSessionRow) -> LoginSessionID:
        return LoginSessionID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_login_sessions_user_id_users",
                error=UserNotFound("The login session's owner does not exist."),
            ),
        )

    @override
    def build_row(self, owner_id: UserID) -> LoginSessionRow:
        return LoginSessionRow(
            user_id=owner_id,
            session_token=self.session_token,
            access_key=self.access_key,
            status=self.status,
        )

    @override
    def to_data(self, row: LoginSessionRow) -> LoginSessionData:
        return row.to_data()


@dataclass
class LoginHistoryCreator(FieldCreator[UserID, LoginHistoryRow, LoginHistoryData]):
    """Creator for one login attempt record, written under the user who made it."""

    domain_name: str
    result: LoginAttemptResult
    fail_reason: str | None = None
    client_ip: str | None = None

    @override
    def field_id(self, row: LoginHistoryRow) -> LoginHistoryID:
        return LoginHistoryID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=ForeignKeyViolationError,
                constraint_name="fk_login_history_user_id_users",
                error=UserNotFound("The login history's owner does not exist."),
            ),
        )

    @override
    def build_row(self, owner_id: UserID) -> LoginHistoryRow:
        return LoginHistoryRow(
            user_id=owner_id,
            domain_name=self.domain_name,
            result=self.result,
            fail_reason=self.fail_reason,
            client_ip=self.client_ip,
        )

    @override
    def to_data(self, row: LoginHistoryRow) -> LoginHistoryData:
        return row.to_data()

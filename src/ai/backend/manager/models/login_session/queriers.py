"""BulkFieldQuerier implementations for the login session and login history tables."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.auth.login_session_types import LoginHistoryData, LoginSessionData
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.models.specs.querier import BulkFieldQuerier


class BulkLoginSessionQuerier(BulkFieldQuerier[LoginSessionRow, LoginSessionData]):
    """The login sessions the caller named."""

    @override
    def row_class(self) -> type[LoginSessionRow]:
        return LoginSessionRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return LoginSessionRow.id

    @override
    def to_data(self, row: LoginSessionRow) -> LoginSessionData:
        return row.to_data()


class BulkLoginHistoryQuerier(BulkFieldQuerier[LoginHistoryRow, LoginHistoryData]):
    """The login history rows the caller named."""

    @override
    def row_class(self) -> type[LoginHistoryRow]:
        return LoginHistoryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return LoginHistoryRow.id

    @override
    def to_data(self, row: LoginHistoryRow) -> LoginHistoryData:
        return row.to_data()

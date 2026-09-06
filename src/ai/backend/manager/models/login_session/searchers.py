"""Searcher specs for the login session and login history tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.auth.login_session_types import LoginHistoryData, LoginSessionData
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class LoginSessionSearcher(Searcher[LoginSessionRow, LoginSessionData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(LoginSessionRow)

    @override
    def to_data(self, row: LoginSessionRow) -> LoginSessionData:
        return row.to_data()


@dataclass
class LoginHistorySearcher(Searcher[LoginHistoryRow, LoginHistoryData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(LoginHistoryRow)

    @override
    def to_data(self, row: LoginHistoryRow) -> LoginHistoryData:
        return row.to_data()

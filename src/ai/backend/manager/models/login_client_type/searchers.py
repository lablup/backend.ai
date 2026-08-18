"""Searcher implementations for the login client type repository."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.login_client_type.types import LoginClientTypeData
from ai.backend.manager.models.login_client_type.row import LoginClientTypeRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class LoginClientTypeSearcher(Searcher[LoginClientTypeRow, LoginClientTypeData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(LoginClientTypeRow)

    @override
    def to_data(self, row: LoginClientTypeRow) -> LoginClientTypeData:
        return row.to_dataclass()

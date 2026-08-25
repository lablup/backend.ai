"""Searcher specs for the users table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.specs.searcher import Searcher
from ai.backend.manager.models.user.row import UserRow


@dataclass
class UserSearcher(Searcher[UserRow, UserData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(UserRow)

    @override
    def to_data(self, row: UserRow) -> UserData:
        return row.to_data()

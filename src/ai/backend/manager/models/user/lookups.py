"""Lookup implementations for the user table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.manager.data.user.types import UserData
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.lookup import DataLookup
from ai.backend.manager.models.user.row import UserRow


@dataclass
class UserEmailLookup(DataLookup[UserRow, UserData]):
    """Resolves a user's email into the user it names."""

    email: str

    @override
    def row_class(self) -> type[UserRow]:
        return UserRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: UserRow.email == self.email]

    @override
    def to_data(self, row: UserRow) -> UserData:
        return row.to_data()

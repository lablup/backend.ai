"""Lookup implementations for the user table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.lookup import DataLookup
from ai.backend.manager.models.user.row import UserRow


@dataclass
class UserEmailLookup(DataLookup[UserRow, UserID]):
    """Resolves a user's email into the user it names."""

    email: str

    @override
    def row_class(self) -> type[UserRow]:
        return UserRow

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: UserRow.email == self.email]

    @override
    def to_entity_id(self, row: UserRow) -> UserID:
        return UserID(row.uuid)

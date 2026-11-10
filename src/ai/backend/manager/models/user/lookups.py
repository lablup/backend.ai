"""Lookup implementations for the user table."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.lookup import BulkDataLookup, DataLookup
from ai.backend.manager.models.user.row import UserRow


@dataclass
class UserEmailLookup(DataLookup[UserRow, UserID]):
    """Resolves a user's email into the user it names."""

    email: str

    @override
    def row_class(self) -> type[UserRow]:
        return UserRow

    @override
    def entity_type(self) -> EntityType:
        return UserEntityType()

    @override
    def conditions(self) -> Sequence[QueryCondition]:
        return [lambda: UserRow.email == self.email]

    @override
    def to_entity_id(self, row: UserRow) -> UserID:
        return UserID(row.uuid)


@dataclass
class UserEmailsLookup(BulkDataLookup[str, UserID]):
    """Resolves several emails into the users they name."""

    @override
    def build_query(self, keys: Sequence[str]) -> sa.sql.Select[Any]:
        return sa.select(UserRow.email, UserRow.uuid).where(UserRow.email.in_(keys))

    @override
    def to_entity_id(self, value: UUID) -> UserID:
        return UserID(value)

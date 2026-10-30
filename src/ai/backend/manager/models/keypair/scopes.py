"""Operation scopes for keypairs."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget
from ai.backend.manager.models.user.row import UserRow

__all__ = ("UserKeypairTarget",)


@dataclass(frozen=True)
class UserKeypairTarget(ScopeTarget):
    """Required scope for searching keypairs owned by a specific user.

    Used for my_keypairs query (current authenticated user).
    """

    user_uuid: UUID
    """Required. The user whose keypairs to search."""

    @override
    def scope_id(self) -> EntityIdentifier:
        return UserID(self.user_uuid)

    @override
    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for KeyPairRow."""
        user_uuid = self.user_uuid

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.user == user_uuid

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_uuid,
                error=UserNotFound(f"User {self.user_uuid} not found"),
            ),
        ]

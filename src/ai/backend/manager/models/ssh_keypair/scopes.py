"""Operation scopes for SSH keypairs."""

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
from ai.backend.manager.models.scopes import ExistenceCheck, ScopeTarget
from ai.backend.manager.models.ssh_keypair.row import SSHKeypairRow
from ai.backend.manager.models.user.row import UserRow

__all__ = ("UserSSHKeypairTarget",)


@dataclass(frozen=True)
class UserSSHKeypairTarget(ScopeTarget):
    """The SSH keypairs a user owns."""

    user_uuid: UUID

    @override
    def scope_id(self) -> EntityIdentifier:
        return UserID(self.user_uuid)

    @override
    def to_condition(self) -> QueryCondition:
        user_uuid = self.user_uuid

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return SSHKeypairRow.user_id == user_uuid

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        return [
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_uuid,
                error=UserNotFound(f"User {self.user_uuid} not found"),
            ),
        ]

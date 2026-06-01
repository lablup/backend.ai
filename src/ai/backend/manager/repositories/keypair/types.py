"""Types for keypair repository operations.

Contains SearchScope dataclasses for keypair search operations.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.user import UserNotFound
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.repositories.base import ExistenceCheck, QueryCondition, SearchScope

__all__ = (
    "UserKeypairSearchScope",
    "KeypairResourcePolicySearchScope",
)


@dataclass(frozen=True)
class UserKeypairSearchScope(SearchScope):
    """Required scope for searching keypairs owned by a specific user.

    Used for my_keypairs query (current authenticated user).
    """

    user_uuid: UUID
    """Required. The user whose keypairs to search."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for KeyPairRow."""
        user_uuid = self.user_uuid

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.user == user_uuid

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[UUID]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=UserRow.uuid,
                value=self.user_uuid,
                error=UserNotFound(f"User {self.user_uuid} not found"),
            ),
        ]


@dataclass(frozen=True)
class KeypairResourcePolicySearchScope(SearchScope):
    """Required scope for searching keypairs assigned to a keypair resource policy.

    Used by the ``keypairs`` connection on the keypair resource policy node.
    RBAC enforcement happens at the action layer (see
    ``SearchKeypairsByResourcePolicyAction``); this scope only constrains the
    query to keypairs whose ``resource_policy`` matches.
    """

    resource_policy_name: str
    """Required. The keypair resource policy whose keypairs to search."""

    def to_condition(self) -> QueryCondition:
        """Convert scope to a query condition for KeyPairRow."""
        resource_policy_name = self.resource_policy_name

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.resource_policy == resource_policy_name

        return inner

    @property
    def existence_checks(self) -> Sequence[ExistenceCheck[str]]:
        """Return existence checks for scope validation."""
        return [
            ExistenceCheck(
                column=KeyPairResourcePolicyRow.name,
                value=self.resource_policy_name,
                error=ObjectNotFound(
                    f"Keypair resource policy '{self.resource_policy_name}' not found"
                ),
            ),
        ]

"""Operation scopes for the keypair resource policy repository."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.models.resource_policy.row import KeyPairResourcePolicyRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope

__all__ = ("UserKeypairResourcePolicyOperationScope",)


@dataclass(frozen=True)
class UserKeypairResourcePolicyOperationScope(OperationScope):
    """The policy one user's default keypair is subject to.

    Picks the keypair marked default, else the earliest active one: the marker is
    backfilled only from the former ``main_access_key`` and can be absent.
    """

    user_id: UserID

    @override
    def to_condition(self) -> QueryCondition:
        user_id = self.user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairResourcePolicyRow.name == (
                sa.select(KeyPairRow.resource_policy)
                .where(KeyPairRow.user == user_id)
                .where(KeyPairRow.is_active.is_(True))
                .order_by(
                    KeyPairRow.is_default.desc(),
                    KeyPairRow.created_at.asc(),
                    KeyPairRow.access_key.asc(),
                )
                .limit(1)
                .scalar_subquery()
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        return ()

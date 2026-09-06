"""Operation scopes for entity invitations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.user.row import UserRow

__all__ = (
    "EntityShareRecipientScope",
    "EntityShareSharerScope",
    "EntityShareTargetScope",
)


@dataclass(frozen=True)
class EntityShareRecipientScope(OperationScope):
    """The invitations addressed to one user.

    The row carries an email rather than a user id, so the requester's own email is
    read back from ``users`` in the condition itself. ``users.email`` is unique, so the
    subquery answers with exactly one value.
    """

    recipient_user_id: UserID

    @override
    def to_condition(self) -> QueryCondition:
        recipient_user_id = self.recipient_user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.recipient_email == (
                sa.select(UserRow.email).where(UserRow.uuid == recipient_user_id).scalar_subquery()
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        # The requester is authenticated before reaching here.
        return ()


@dataclass(frozen=True)
class EntityShareSharerScope(OperationScope):
    """The invitations one user sent."""

    sharer_user_id: UserID

    @override
    def to_condition(self) -> QueryCondition:
        sharer_user_id = self.sharer_user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.sharer_user_id == sharer_user_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        # The requester is authenticated before reaching here.
        return ()


@dataclass(frozen=True)
class EntityShareTargetScope(OperationScope):
    """The invitations offering one entity."""

    target: EntityIdentifier

    @override
    def to_condition(self) -> QueryCondition:
        target = self.target

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                EntityShareRow.target_entity_type == target.entity_type(),
                EntityShareRow.target_entity_id == target,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        # The target's readability is settled by the permission check before this runs.
        return ()

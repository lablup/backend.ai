"""Operation scopes for entity invitations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_invitation.row import EntityInvitationRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.user.row import UserRow

__all__ = (
    "EntityInvitationInviteeScope",
    "EntityInvitationInviterScope",
    "EntityInvitationTargetScope",
)


@dataclass(frozen=True)
class EntityInvitationInviteeScope(OperationScope):
    """The invitations addressed to one user.

    The row carries an email rather than a user id, so the requester's own email is
    read back from ``users`` in the condition itself. ``users.email`` is unique, so the
    subquery answers with exactly one value.
    """

    invitee_user_id: UserID

    @override
    def to_condition(self) -> QueryCondition:
        invitee_user_id = self.invitee_user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityInvitationRow.invitee_email == (
                sa.select(UserRow.email).where(UserRow.uuid == invitee_user_id).scalar_subquery()
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        # The requester is authenticated before reaching here.
        return ()


@dataclass(frozen=True)
class EntityInvitationInviterScope(OperationScope):
    """The invitations one user sent."""

    inviter_user_id: UserID

    @override
    def to_condition(self) -> QueryCondition:
        inviter_user_id = self.inviter_user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityInvitationRow.inviter_user_id == inviter_user_id

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        # The requester is authenticated before reaching here.
        return ()


@dataclass(frozen=True)
class EntityInvitationTargetScope(OperationScope):
    """The invitations offering one entity."""

    target: EntityIdentifier

    @override
    def to_condition(self) -> QueryCondition:
        target = self.target

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                EntityInvitationRow.target_entity_type == target.entity_type(),
                EntityInvitationRow.target_entity_id == target,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        # The target's readability is settled by the permission check before this runs.
        return ()

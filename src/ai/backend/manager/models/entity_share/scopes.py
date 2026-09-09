"""Operation scopes for entity invitations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.user.row import UserRow

__all__ = (
    "EntityShareRecipientProjectScope",
    "EntityShareRecipientScope",
    "EntityShareSharerScope",
    "EntityShareTargetScope",
)


@dataclass(frozen=True)
class EntityShareRecipientScope(OperationScope):
    """The offers addressed to one person, whichever way they were named.

    A person is named two ways: by who they are, and by an address that reached them
    before they had an account. Both are read back inside the statement — the node they
    hold from ``virtual_entities``, their address from ``users``, where the column is
    unique and answers with one value.
    """

    recipient_user_id: UserID

    @override
    def to_condition(self) -> QueryCondition:
        recipient_user_id = self.recipient_user_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.or_(
                EntityShareRow.recipient_email
                == (
                    sa.select(UserRow.email)
                    .where(UserRow.uuid == recipient_user_id)
                    .scalar_subquery()
                ),
                sa.and_(
                    EntityShareRow.recipient_entity_type == UserEntityType(),
                    EntityShareRow.recipient_entity_id == recipient_user_id,
                ),
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        # The requester is authenticated before reaching here.
        return ()


@dataclass(frozen=True)
class EntityShareRecipientProjectScope(OperationScope):
    """The offers addressed to one project."""

    project_id: ProjectID

    @override
    def to_condition(self) -> QueryCondition:
        project_id = self.project_id

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                EntityShareRow.recipient_entity_type == ProjectEntityType(),
                EntityShareRow.recipient_entity_id == project_id,
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        # The project's readability is settled by the permission check before this runs.
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

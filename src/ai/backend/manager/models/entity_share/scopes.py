"""Operation scopes for entity invitations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.entity_share import EntityShareEntityType
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_share.row import EntityShareRow
from ai.backend.manager.models.scopes import ExistenceCheck, OperationScope
from ai.backend.manager.models.user.queries import user_scope_reaches
from ai.backend.manager.models.user.row import UserRow
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists

__all__ = (
    "EntityShareOwningScope",
    "EntityShareRecipientProjectScope",
    "EntityShareRecipientScope",
)


@dataclass(frozen=True)
class EntityShareRecipientScope(OperationScope):
    """The offers addressed to one person, whichever way they were named.

    The one read that cannot go through the ownership graph: an offer may name an
    address that belongs to no account yet, and an address holds no node.

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
class EntityShareOwningScope(OperationScope):
    """The offers a scope reaches, through the entity each offer is attached to.

    An offer is created in the entity it offers, so who reaches the offer is who
    reaches that entity -- a user, a project, a domain, or the entity itself, told
    apart by nothing but the scope handed in.
    """

    scope: EntityIdentifier

    @override
    def to_condition(self) -> QueryCondition:
        scope = self.scope

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if isinstance(scope, UserID):
                return user_scope_reaches(scope, EntityShareEntityType(), EntityShareRow.id)
            return scope_membership_exists(
                scope.entity_type(), scope, EntityShareEntityType(), EntityShareRow.id
            )

        return inner

    @property
    @override
    def existence_checks(self) -> Sequence[ExistenceCheck[Any]]:
        # The scope's readability is settled by the permission check before this runs.
        return ()

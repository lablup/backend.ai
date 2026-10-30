"""Conditions on where an entity sits in the ownership graph."""

from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.user import UserID
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.specs.conditions.types import FilterColumn
from ai.backend.manager.models.user.queries import user_scope_shares
from ai.backend.manager.models.virtual_entity.queries import scope_membership_exists


class MembershipConditions:
    """Graph membership of the entity whose id is in ``member_id``."""

    _member_type: EntityType
    _member_id: FilterColumn

    def __init__(self, member_type: EntityType, member_id: FilterColumn) -> None:
        self._member_type = member_type
        self._member_id = member_id

    def reached_by(self, scope_type: EntityType, scope_id: uuid.UUID) -> QueryCondition:
        """The scope reaches the entity, the span a permission check walks."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return scope_membership_exists(scope_type, scope_id, self._member_type, self._member_id)

        return inner

    def shared_to(self, user_id: UserID) -> QueryCondition:
        """The entity was shared to the user or their personal project."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return user_scope_shares(user_id, self._member_type, self._member_id)

        return inner

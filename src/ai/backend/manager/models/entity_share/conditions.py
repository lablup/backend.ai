"""Query conditions for entity invitation rows."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.entity_share.types import EntityShareStatus
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.entity_share.row import EntityShareRow

__all__ = ("EntityShareConditions",)


class EntityShareConditions:
    @staticmethod
    def by_ids(ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.id.in_(ids)

        return inner

    @staticmethod
    def by_sharers(user_ids: Collection[uuid.UUID]) -> QueryCondition:
        """Narrows to the offers those people sent, within a scope already answered for."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.sharer_user_id.in_(user_ids)

        return inner

    @staticmethod
    def by_status(status: EntityShareStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.status == status

        return inner

    @staticmethod
    def by_status_in(statuses: Collection[EntityShareStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_recipient_email(email: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.recipient_email == email

        return inner

    @staticmethod
    def by_recipient(recipient: EntityIdentifier) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                EntityShareRow.recipient_entity_type == recipient.entity_type(),
                EntityShareRow.recipient_entity_id == recipient,
            )

        return inner

    @staticmethod
    def by_target(target: EntityIdentifier) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                EntityShareRow.target_entity_type == target.entity_type(),
                EntityShareRow.target_entity_id == target,
            )

        return inner

    @staticmethod
    def by_target_entity_type(entity_type: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EntityShareRow.target_entity_type == entity_type

        return inner

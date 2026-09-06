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

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Compares against the cursor row's ``created_at``, which is what the page is
        ordered by.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(EntityShareRow.created_at)
                .where(EntityShareRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return EntityShareRow.created_at > subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor)."""
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(EntityShareRow.created_at)
                .where(EntityShareRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return EntityShareRow.created_at < subquery

        return inner

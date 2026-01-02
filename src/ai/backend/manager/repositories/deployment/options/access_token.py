"""Query conditions and orders for access tokens."""

from __future__ import annotations

import uuid
from collections.abc import Collection
from datetime import datetime

import sqlalchemy as sa

from ai.backend.manager.models.endpoint import EndpointTokenRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


class AccessTokenConditions:
    """Query conditions for access tokens."""

    @staticmethod
    def by_ids(token_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.id.in_(token_ids)

        return inner

    @staticmethod
    def by_endpoint_id(endpoint_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.endpoint == endpoint_id

        return inner

    # Token string conditions
    @staticmethod
    def by_token_equals(value: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.token == value

        return inner

    @staticmethod
    def by_token_contains(value: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.token.contains(value)

        return inner

    # valid_until datetime conditions
    @staticmethod
    def by_valid_until_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.valid_until < dt

        return inner

    @staticmethod
    def by_valid_until_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.valid_until > dt

        return inner

    @staticmethod
    def by_valid_until_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.valid_until == dt

        return inner

    # created_at datetime conditions
    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointTokenRow.created_at == dt

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(EndpointTokenRow.created_at)
                .where(EndpointTokenRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return EndpointTokenRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(EndpointTokenRow.created_at)
                .where(EndpointTokenRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return EndpointTokenRow.created_at > subquery

        return inner


class AccessTokenOrders:
    """Query orders for access tokens."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointTokenRow.created_at.asc()
        else:
            return EndpointTokenRow.created_at.desc()

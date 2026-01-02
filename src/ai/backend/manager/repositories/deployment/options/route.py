"""Query conditions and orders for routes."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.data.deployment.types import RouteStatus, RouteTrafficStatus
from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


class RouteConditions:
    """Query conditions for routes."""

    @staticmethod
    def by_ids(route_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoutingRow.id.in_(route_ids)

        return inner

    @staticmethod
    def by_endpoint_id(endpoint_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoutingRow.endpoint == endpoint_id

        return inner

    @staticmethod
    def by_statuses(statuses: list[RouteStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoutingRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_traffic_statuses(traffic_statuses: list[RouteTrafficStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoutingRow.traffic_status.in_(traffic_statuses)

        return inner

    @staticmethod
    def by_revision_ids(revision_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoutingRow.revision.in_(revision_ids)

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RoutingRow.created_at)
                .where(RoutingRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return RoutingRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RoutingRow.created_at)
                .where(RoutingRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return RoutingRow.created_at > subquery

        return inner


class RouteOrders:
    """Query orders for routes."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoutingRow.created_at.asc()
        else:
            return RoutingRow.created_at.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoutingRow.status.asc()
        else:
            return RoutingRow.status.desc()

    @staticmethod
    def traffic_ratio(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoutingRow.traffic_ratio.asc()
        else:
            return RoutingRow.traffic_ratio.desc()

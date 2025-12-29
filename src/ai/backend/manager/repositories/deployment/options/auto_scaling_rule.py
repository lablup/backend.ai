"""Query conditions and orders for auto-scaling rules."""

from __future__ import annotations

import uuid
from collections.abc import Collection
from datetime import datetime

import sqlalchemy as sa

from ai.backend.manager.models.endpoint import EndpointAutoScalingRuleRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


class AutoScalingRuleConditions:
    """Query conditions for auto-scaling rules."""

    @staticmethod
    def by_ids(rule_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.id.in_(rule_ids)

        return inner

    @staticmethod
    def by_endpoint_id(endpoint_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.endpoint == endpoint_id

        return inner

    @staticmethod
    def by_deployment_id(deployment_id: uuid.UUID) -> QueryCondition:
        """Alias for by_endpoint_id for consistency with deployment naming."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.endpoint == deployment_id

        return inner

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.created_at == dt

        return inner

    @staticmethod
    def by_last_triggered_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.last_triggered_at < dt

        return inner

    @staticmethod
    def by_last_triggered_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.last_triggered_at > dt

        return inner

    @staticmethod
    def by_last_triggered_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return EndpointAutoScalingRuleRow.last_triggered_at == dt

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(EndpointAutoScalingRuleRow.created_at)
                .where(EndpointAutoScalingRuleRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return EndpointAutoScalingRuleRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(EndpointAutoScalingRuleRow.created_at)
                .where(EndpointAutoScalingRuleRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return EndpointAutoScalingRuleRow.created_at > subquery

        return inner


class AutoScalingRuleOrders:
    """Query orders for auto-scaling rules."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointAutoScalingRuleRow.created_at.asc()
        else:
            return EndpointAutoScalingRuleRow.created_at.desc()

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.data.notification import NotificationChannelType, NotificationRuleType
from ai.backend.manager.models.notification import NotificationChannelRow, NotificationRuleRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


class NotificationChannelConditions:
    """Query conditions for notification channels."""

    @staticmethod
    def by_ids(channel_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return NotificationChannelRow.id.in_(channel_ids)

        return inner

    @staticmethod
    def by_name_contains(name: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return NotificationChannelRow.name.ilike(f"%{name}%")
            else:
                return NotificationChannelRow.name.like(f"%{name}%")

        return inner

    @staticmethod
    def by_name_equals(name: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(NotificationChannelRow.name) == name.lower()
            else:
                return NotificationChannelRow.name == name

        return inner

    @staticmethod
    def by_channel_types(channel_types: list[NotificationChannelType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return NotificationChannelRow.channel_type.in_(channel_types)

        return inner

    @staticmethod
    def by_enabled(enabled: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return NotificationChannelRow.enabled == enabled

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(NotificationChannelRow.created_at)
                .where(NotificationChannelRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return NotificationChannelRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(NotificationChannelRow.created_at)
                .where(NotificationChannelRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return NotificationChannelRow.created_at > subquery

        return inner


class NotificationChannelOrders:
    """Query orders for notification channels."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationChannelRow.name.asc()
        else:
            return NotificationChannelRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationChannelRow.created_at.asc()
        else:
            return NotificationChannelRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationChannelRow.updated_at.asc()
        else:
            return NotificationChannelRow.updated_at.desc()


class NotificationRuleConditions:
    """Query conditions for notification rules."""

    @staticmethod
    def by_ids(rule_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return NotificationRuleRow.id.in_(rule_ids)

        return inner

    @staticmethod
    def by_name_contains(name: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return NotificationRuleRow.name.ilike(f"%{name}%")
            else:
                return NotificationRuleRow.name.like(f"%{name}%")

        return inner

    @staticmethod
    def by_name_equals(name: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(NotificationRuleRow.name) == name.lower()
            else:
                return NotificationRuleRow.name == name

        return inner

    @staticmethod
    def by_rule_types(rule_types: list[NotificationRuleType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return NotificationRuleRow.rule_type.in_(rule_types)

        return inner

    @staticmethod
    def by_enabled(enabled: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return NotificationRuleRow.enabled == enabled

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(NotificationRuleRow.created_at)
                .where(NotificationRuleRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return NotificationRuleRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(NotificationRuleRow.created_at)
                .where(NotificationRuleRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return NotificationRuleRow.created_at > subquery

        return inner


class NotificationRuleOrders:
    """Query orders for notification rules."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationRuleRow.name.asc()
        else:
            return NotificationRuleRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationRuleRow.created_at.asc()
        else:
            return NotificationRuleRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationRuleRow.updated_at.asc()
        else:
            return NotificationRuleRow.updated_at.desc()

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.notification import NotificationChannelType, NotificationRuleType
from ai.backend.manager.api.gql.base import StringMatchSpec
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
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NotificationChannelRow.name.ilike(f"%{spec.value}%")
            else:
                condition = NotificationChannelRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(NotificationChannelRow.name) == spec.value.lower()
            else:
                condition = NotificationChannelRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NotificationChannelRow.name.ilike(f"{spec.value}%")
            else:
                condition = NotificationChannelRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NotificationChannelRow.name.ilike(f"%{spec.value}")
            else:
                condition = NotificationChannelRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

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
        return NotificationChannelRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationChannelRow.created_at.asc()
        return NotificationChannelRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationChannelRow.updated_at.asc()
        return NotificationChannelRow.updated_at.desc()


class NotificationRuleConditions:
    """Query conditions for notification rules."""

    @staticmethod
    def by_ids(rule_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return NotificationRuleRow.id.in_(rule_ids)

        return inner

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NotificationRuleRow.name.ilike(f"%{spec.value}%")
            else:
                condition = NotificationRuleRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(NotificationRuleRow.name) == spec.value.lower()
            else:
                condition = NotificationRuleRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NotificationRuleRow.name.ilike(f"{spec.value}%")
            else:
                condition = NotificationRuleRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = NotificationRuleRow.name.ilike(f"%{spec.value}")
            else:
                condition = NotificationRuleRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

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
        return NotificationRuleRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationRuleRow.created_at.asc()
        return NotificationRuleRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return NotificationRuleRow.updated_at.asc()
        return NotificationRuleRow.updated_at.desc()

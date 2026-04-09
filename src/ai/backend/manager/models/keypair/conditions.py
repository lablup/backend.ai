"""Query conditions and orders for keypair entities."""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.keypair.row import KeyPairRow
from ai.backend.manager.repositories.base.types import QueryCondition, QueryOrder

__all__ = (
    "KeypairConditions",
    "KeypairOrders",
)


class KeypairConditions:
    """Query conditions for filtering keypairs."""

    @staticmethod
    def by_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.is_active == is_active

        return inner

    @staticmethod
    def by_is_admin(is_admin: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.is_admin == is_admin

        return inner

    @staticmethod
    def by_access_key_equals(spec: StringMatchSpec) -> QueryCondition:
        value = spec.value
        negated = spec.negated
        case_insensitive = spec.case_insensitive

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                cond: sa.sql.expression.ColumnElement[bool] = KeyPairRow.access_key.ilike(value)
            else:
                cond = KeyPairRow.access_key == value
            if negated:
                return sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_access_key_contains(spec: StringMatchSpec) -> QueryCondition:
        value = spec.value
        negated = spec.negated
        case_insensitive = spec.case_insensitive

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                cond: sa.sql.expression.ColumnElement[bool] = KeyPairRow.access_key.ilike(
                    f"%{value}%"
                )
            else:
                cond = KeyPairRow.access_key.contains(value)
            if negated:
                return sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_access_key_starts_with(spec: StringMatchSpec) -> QueryCondition:
        value = spec.value
        negated = spec.negated
        case_insensitive = spec.case_insensitive

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                cond: sa.sql.expression.ColumnElement[bool] = KeyPairRow.access_key.ilike(
                    f"{value}%"
                )
            else:
                cond = KeyPairRow.access_key.like(f"{value}%")
            if negated:
                return sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_access_key_ends_with(spec: StringMatchSpec) -> QueryCondition:
        value = spec.value
        negated = spec.negated
        case_insensitive = spec.case_insensitive

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                cond: sa.sql.expression.ColumnElement[bool] = KeyPairRow.access_key.ilike(
                    f"%{value}"
                )
            else:
                cond = KeyPairRow.access_key.like(f"%{value}")
            if negated:
                return sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_resource_policy_equals(spec: StringMatchSpec) -> QueryCondition:
        value = spec.value
        negated = spec.negated
        case_insensitive = spec.case_insensitive

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                cond: sa.sql.expression.ColumnElement[bool] = KeyPairRow.resource_policy.ilike(
                    value
                )
            else:
                cond = KeyPairRow.resource_policy == value
            if negated:
                return sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_resource_policy_contains(spec: StringMatchSpec) -> QueryCondition:
        value = spec.value
        negated = spec.negated
        case_insensitive = spec.case_insensitive

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                cond: sa.sql.expression.ColumnElement[bool] = KeyPairRow.resource_policy.ilike(
                    f"%{value}%"
                )
            else:
                cond = KeyPairRow.resource_policy.contains(value)
            if negated:
                return sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_resource_policy_starts_with(spec: StringMatchSpec) -> QueryCondition:
        value = spec.value
        negated = spec.negated
        case_insensitive = spec.case_insensitive

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                cond: sa.sql.expression.ColumnElement[bool] = KeyPairRow.resource_policy.ilike(
                    f"{value}%"
                )
            else:
                cond = KeyPairRow.resource_policy.like(f"{value}%")
            if negated:
                return sa.not_(cond)
            return cond

        return inner

    @staticmethod
    def by_resource_policy_ends_with(spec: StringMatchSpec) -> QueryCondition:
        value = spec.value
        negated = spec.negated
        case_insensitive = spec.case_insensitive

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                cond: sa.sql.expression.ColumnElement[bool] = KeyPairRow.resource_policy.ilike(
                    f"%{value}"
                )
            else:
                cond = KeyPairRow.resource_policy.like(f"%{value}")
            if negated:
                return sa.not_(cond)
            return cond

        return inner

    by_access_key_in = staticmethod(make_string_in_factory(KeyPairRow.access_key))
    by_resource_policy_in = staticmethod(make_string_in_factory(KeyPairRow.resource_policy))

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.created_at <= dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.created_at >= dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.created_at == dt

        return inner

    @staticmethod
    def by_last_used_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.last_used <= dt

        return inner

    @staticmethod
    def by_last_used_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.last_used >= dt

        return inner

    @staticmethod
    def by_last_used_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KeyPairRow.last_used == dt

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to look up created_at of the cursor row (default order: created_at DESC).
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(KeyPairRow.created_at)
                .where(KeyPairRow.access_key == cursor_id)
                .scalar_subquery()
            )
            return KeyPairRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to look up created_at of the cursor row (default order: created_at DESC).
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(KeyPairRow.created_at)
                .where(KeyPairRow.access_key == cursor_id)
                .scalar_subquery()
            )
            return KeyPairRow.created_at > subquery

        return inner


class KeypairOrders:
    """Query orders for sorting keypairs."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairRow.created_at.asc()
        return KeyPairRow.created_at.desc()

    @staticmethod
    def last_used(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairRow.last_used.asc()
        return KeyPairRow.last_used.desc()

    @staticmethod
    def access_key(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairRow.access_key.asc()
        return KeyPairRow.access_key.desc()

    @staticmethod
    def is_active(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairRow.is_active.asc()
        return KeyPairRow.is_active.desc()

    @staticmethod
    def resource_policy(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KeyPairRow.resource_policy.asc()
        return KeyPairRow.resource_policy.desc()

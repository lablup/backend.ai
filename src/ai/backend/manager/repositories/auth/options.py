from __future__ import annotations

import uuid
from collections.abc import Collection
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa

from ai.backend.manager.models.condition_utils import make_string_in_factory
from ai.backend.manager.models.login_session.enums import LoginAttemptResult, LoginSessionStatus
from ai.backend.manager.models.login_session.row import LoginHistoryRow, LoginSessionRow
from ai.backend.manager.repositories.base.types import QueryCondition, QueryOrder

if TYPE_CHECKING:
    from ai.backend.common.data.filter_specs import StringMatchSpec


class LoginSessionConditions:
    """Query conditions for login sessions."""

    @staticmethod
    def by_ids(session_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginSessionRow.id.in_(session_ids)

        return inner

    # --- status enum filters ---

    @staticmethod
    def by_status_equals(status: str | LoginSessionStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginSessionRow.status == status

        return inner

    @staticmethod
    def by_status_in(statuses: Collection[str | LoginSessionStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginSessionRow.status.in_(statuses)

        return inner

    @staticmethod
    def by_status_not_in(statuses: Collection[str | LoginSessionStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginSessionRow.status.notin_(statuses)

        return inner

    # --- access_key string filters ---

    @staticmethod
    def by_access_key_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LoginSessionRow.access_key.ilike(f"%{spec.value}%")
            else:
                condition = LoginSessionRow.access_key.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_access_key_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(LoginSessionRow.access_key) == spec.value.lower()
            else:
                condition = LoginSessionRow.access_key == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_access_key_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LoginSessionRow.access_key.ilike(f"{spec.value}%")
            else:
                condition = LoginSessionRow.access_key.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_access_key_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LoginSessionRow.access_key.ilike(f"%{spec.value}")
            else:
                condition = LoginSessionRow.access_key.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_access_key_in = staticmethod(make_string_in_factory(LoginSessionRow.access_key))

    # --- created_at datetime filters ---

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginSessionRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginSessionRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginSessionRow.created_at == dt

        return inner

    # --- last_accessed_at datetime filters ---

    @staticmethod
    def by_last_accessed_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginSessionRow.last_accessed_at < dt

        return inner

    @staticmethod
    def by_last_accessed_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginSessionRow.last_accessed_at > dt

        return inner

    @staticmethod
    def by_last_accessed_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginSessionRow.last_accessed_at == dt

        return inner

    # --- cursor pagination conditions ---

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(LoginSessionRow.created_at)
                .where(LoginSessionRow.id == cursor_id)
                .scalar_subquery()
            )
            return LoginSessionRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(LoginSessionRow.created_at)
                .where(LoginSessionRow.id == cursor_id)
                .scalar_subquery()
            )
            return LoginSessionRow.created_at > subquery

        return inner


class LoginSessionOrders:
    """Query orders for login sessions."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return LoginSessionRow.created_at.asc()
        return LoginSessionRow.created_at.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return LoginSessionRow.status.asc()
        return LoginSessionRow.status.desc()

    @staticmethod
    def last_accessed_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return LoginSessionRow.last_accessed_at.asc()
        return LoginSessionRow.last_accessed_at.desc()


class LoginHistoryConditions:
    """Query conditions for login history."""

    @staticmethod
    def by_ids(history_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginHistoryRow.id.in_(history_ids)

        return inner

    # --- result enum filters ---

    @staticmethod
    def by_result_equals(result: str | LoginAttemptResult) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginHistoryRow.result == result

        return inner

    @staticmethod
    def by_result_in(results: Collection[str | LoginAttemptResult]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginHistoryRow.result.in_(results)

        return inner

    @staticmethod
    def by_result_not_in(results: Collection[str | LoginAttemptResult]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginHistoryRow.result.notin_(results)

        return inner

    # --- domain_name string filters ---

    @staticmethod
    def by_domain_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LoginHistoryRow.domain_name.ilike(f"%{spec.value}%")
            else:
                condition = LoginHistoryRow.domain_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(LoginHistoryRow.domain_name) == spec.value.lower()
            else:
                condition = LoginHistoryRow.domain_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LoginHistoryRow.domain_name.ilike(f"{spec.value}%")
            else:
                condition = LoginHistoryRow.domain_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = LoginHistoryRow.domain_name.ilike(f"%{spec.value}")
            else:
                condition = LoginHistoryRow.domain_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_domain_name_in = staticmethod(make_string_in_factory(LoginHistoryRow.domain_name))

    # --- created_at datetime filters ---

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginHistoryRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginHistoryRow.created_at > dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return LoginHistoryRow.created_at == dt

        return inner

    # --- cursor pagination conditions ---

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(LoginHistoryRow.created_at)
                .where(LoginHistoryRow.id == cursor_id)
                .scalar_subquery()
            )
            return LoginHistoryRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(LoginHistoryRow.created_at)
                .where(LoginHistoryRow.id == cursor_id)
                .scalar_subquery()
            )
            return LoginHistoryRow.created_at > subquery

        return inner


class LoginHistoryOrders:
    """Query orders for login history."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return LoginHistoryRow.created_at.asc()
        return LoginHistoryRow.created_at.desc()

    @staticmethod
    def result(ascending: bool = True) -> QueryOrder:
        if ascending:
            return LoginHistoryRow.result.asc()
        return LoginHistoryRow.result.desc()

    @staticmethod
    def domain_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return LoginHistoryRow.domain_name.asc()
        return LoginHistoryRow.domain_name.desc()

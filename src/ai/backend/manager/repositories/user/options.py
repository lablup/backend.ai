"""Query conditions and orders for user repository operations."""

from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

__all__ = (
    "UserConditions",
    "UserOrders",
)


class UserConditions:
    """Query conditions for filtering users."""

    # ==================== Email Filters ====================

    @staticmethod
    def by_email_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.email.ilike(f"%{spec.value}%")
            else:
                condition = UserRow.email.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_email_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(UserRow.email) == spec.value.lower()
            else:
                condition = UserRow.email == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_email_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.email.ilike(f"{spec.value}%")
            else:
                condition = UserRow.email.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_email_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.email.ilike(f"%{spec.value}")
            else:
                condition = UserRow.email.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ==================== Username Filters ====================

    @staticmethod
    def by_username_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.username.ilike(f"%{spec.value}%")
            else:
                condition = UserRow.username.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_username_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(UserRow.username) == spec.value.lower()
            else:
                condition = UserRow.username == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_username_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.username.ilike(f"{spec.value}%")
            else:
                condition = UserRow.username.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_username_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.username.ilike(f"%{spec.value}")
            else:
                condition = UserRow.username.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ==================== Domain Name Filters ====================

    @staticmethod
    def by_domain_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.domain_name.ilike(f"%{spec.value}%")
            else:
                condition = UserRow.domain_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(UserRow.domain_name) == spec.value.lower()
            else:
                condition = UserRow.domain_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.domain_name.ilike(f"{spec.value}%")
            else:
                condition = UserRow.domain_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.domain_name.ilike(f"%{spec.value}")
            else:
                condition = UserRow.domain_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ==================== Status Filters ====================

    @staticmethod
    def by_status_equals(status: UserStatus) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.status == status

        return inner

    @staticmethod
    def by_status_in(statuses: Collection[UserStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.status.in_(statuses)

        return inner

    # ==================== Role Filters ====================

    @staticmethod
    def by_role_equals(role: UserRole) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.role == role

        return inner

    @staticmethod
    def by_role_in(roles: Collection[UserRole]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.role.in_(roles)

        return inner

    # ==================== Cursor Pagination ====================

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(UserRow.created_at).where(UserRow.uuid == cursor_id).scalar_subquery()
            )
            return UserRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(UserRow.created_at).where(UserRow.uuid == cursor_id).scalar_subquery()
            )
            return UserRow.created_at > subquery

        return inner


class UserOrders:
    """Query orders for sorting users."""

    @staticmethod
    def uuid(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.uuid.asc()
        return UserRow.uuid.desc()

    @staticmethod
    def email(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.email.asc()
        return UserRow.email.desc()

    @staticmethod
    def username(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.username.asc()
        return UserRow.username.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.created_at.asc()
        return UserRow.created_at.desc()

    @staticmethod
    def modified_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.modified_at.asc()
        return UserRow.modified_at.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.status.asc()
        return UserRow.status.desc()

    @staticmethod
    def domain_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.domain_name.asc()
        return UserRow.domain_name.desc()

"""Query conditions and orders for user repository operations."""

from __future__ import annotations

from collections.abc import Collection
from datetime import datetime
from typing import Any

import sqlalchemy as sa

from ai.backend.common.data.user.types import UserRole
from ai.backend.manager.api.gql.base import StringMatchSpec, UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
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

    # ==================== UUID Filters ====================

    @staticmethod
    def by_uuid_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        """Filter by UUID equality.

        Args:
            spec: UUID equality specification with value and negated flag.

        Returns:
            QueryCondition callable for UUID filtering.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = UserRow.uuid == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_uuid_in(spec: UUIDInMatchSpec) -> QueryCondition:
        """Filter by UUID IN operation.

        Args:
            spec: UUID IN specification with values list and negated flag.

        Returns:
            QueryCondition callable for UUID IN filtering.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = UserRow.uuid.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ==================== DateTime Filters ====================

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        """Filter by created_at < datetime."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        """Filter by created_at > datetime."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.created_at > dt

        return inner

    @staticmethod
    def by_modified_at_before(dt: datetime) -> QueryCondition:
        """Filter by modified_at < datetime."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.modified_at < dt

        return inner

    @staticmethod
    def by_modified_at_after(dt: datetime) -> QueryCondition:
        """Filter by modified_at > datetime."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.modified_at > dt

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

    # ==================== Domain Nested Filters ====================

    @staticmethod
    def _exists_domain(
        *domain_conditions: sa.sql.expression.ColumnElement[bool],
    ) -> sa.sql.expression.ColumnElement[bool]:
        """EXISTS subquery: User → Domain (via FK domain_name)."""
        subq = sa.select(sa.literal(1)).where(DomainRow.name == UserRow.domain_name)
        for cond in domain_conditions:
            subq = subq.where(cond)
        return sa.exists(subq)

    @staticmethod
    def by_domain_description_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = DomainRow.description.ilike(f"%{spec.value}%")
            else:
                cond = DomainRow.description.like(f"%{spec.value}%")
            if spec.negated:
                cond = sa.not_(cond)
            return UserConditions._exists_domain(cond)

        return inner

    @staticmethod
    def by_domain_description_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = sa.func.lower(DomainRow.description) == spec.value.lower()
            else:
                cond = DomainRow.description == spec.value
            if spec.negated:
                cond = sa.not_(cond)
            return UserConditions._exists_domain(cond)

        return inner

    @staticmethod
    def by_domain_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserConditions._exists_domain(DomainRow.is_active == is_active)

        return inner

    @staticmethod
    def exists_domain_combined(domain_conditions: list[QueryCondition]) -> QueryCondition:
        """Combine multiple domain conditions into single EXISTS subquery.

        Accepts conditions from DomainV2Filter.build_conditions() directly.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(DomainRow.name == UserRow.domain_name)
            for cond in domain_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner

    # ==================== Project Nested Filters (M:N) ====================

    @staticmethod
    def _exists_project(
        *project_conditions: sa.sql.expression.ColumnElement[bool],
    ) -> sa.sql.expression.ColumnElement[bool]:
        """EXISTS subquery: User → Project (via M:N AssocGroupUserRow)."""
        subq = (
            sa.select(sa.literal(1))
            .select_from(
                sa.join(
                    AssocGroupUserRow.__table__,
                    GroupRow.__table__,
                    AssocGroupUserRow.group_id == GroupRow.id,
                )
            )
            .where(AssocGroupUserRow.user_id == UserRow.uuid)
        )
        for cond in project_conditions:
            subq = subq.where(cond)
        return sa.exists(subq)

    @staticmethod
    def by_project_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = GroupRow.name.ilike(f"%{spec.value}%")
            else:
                cond = GroupRow.name.like(f"%{spec.value}%")
            if spec.negated:
                cond = sa.not_(cond)
            return UserConditions._exists_project(cond)

        return inner

    @staticmethod
    def by_project_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = sa.func.lower(GroupRow.name) == spec.value.lower()
            else:
                cond = GroupRow.name == spec.value
            if spec.negated:
                cond = sa.not_(cond)
            return UserConditions._exists_project(cond)

        return inner

    @staticmethod
    def by_project_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserConditions._exists_project(GroupRow.is_active == is_active)

        return inner

    @staticmethod
    def exists_project_combined(project_conditions: list[QueryCondition]) -> QueryCondition:
        """Combine multiple project conditions into single EXISTS subquery.

        Accepts conditions from ProjectV2Filter.build_conditions() directly.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = (
                sa.select(sa.literal(1))
                .select_from(
                    sa.join(
                        AssocGroupUserRow.__table__,
                        GroupRow.__table__,
                        AssocGroupUserRow.group_id == GroupRow.id,
                    )
                )
                .where(AssocGroupUserRow.user_id == UserRow.uuid)
            )
            for cond in project_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

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

    # ==================== Domain Nested Orders ====================

    @staticmethod
    def _scalar_domain(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        """Scalar subquery selecting a Domain column correlated to current User."""
        return (
            sa.select(column)
            .where(DomainRow.name == UserRow.domain_name)
            .correlate(UserRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_domain_name(ascending: bool = True) -> QueryOrder:
        subq = UserOrders._scalar_domain(DomainRow.name)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_domain_created_at(ascending: bool = True) -> QueryOrder:
        subq = UserOrders._scalar_domain(DomainRow.created_at)
        return subq.asc() if ascending else subq.desc()

    # ==================== Project Nested Orders (M:N → MIN aggregation) ====================

    @staticmethod
    def _scalar_project_min(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        """Scalar subquery with MIN for M:N relationship."""
        return (
            sa.select(sa.func.min(column))
            .select_from(
                sa.join(
                    AssocGroupUserRow.__table__,
                    GroupRow.__table__,
                    AssocGroupUserRow.group_id == GroupRow.id,
                )
            )
            .where(AssocGroupUserRow.user_id == UserRow.uuid)
            .correlate(UserRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_project_name(ascending: bool = True) -> QueryOrder:
        subq = UserOrders._scalar_project_min(GroupRow.name)
        return subq.asc() if ascending else subq.desc()

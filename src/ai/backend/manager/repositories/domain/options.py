"""Query conditions and orders for domain repository operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.scaling_group import ScalingGroupForDomainRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

__all__ = (
    "DomainConditions",
    "DomainOrders",
)


class DomainConditions:
    """Query conditions for filtering domains."""

    # ==================== Name Filters ====================

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.name.ilike(f"%{spec.value}%")
            else:
                condition = DomainRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(DomainRow.name) == spec.value.lower()
            else:
                condition = DomainRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.name.ilike(f"{spec.value}%")
            else:
                condition = DomainRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.name.ilike(f"%{spec.value}")
            else:
                condition = DomainRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ==================== Description Filters ====================

    @staticmethod
    def by_description_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.description.ilike(f"%{spec.value}%")
            else:
                condition = DomainRow.description.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(DomainRow.description) == spec.value.lower()
            else:
                condition = DomainRow.description == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.description.ilike(f"{spec.value}%")
            else:
                condition = DomainRow.description.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_description_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.description.ilike(f"%{spec.value}")
            else:
                condition = DomainRow.description.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ==================== Active Status Filters ====================

    @staticmethod
    def by_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.is_active == is_active

        return inner

    # ==================== Integration ID Filters ====================

    @staticmethod
    def by_integration_id_equals(integration_id: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.integration_id == integration_id

        return inner

    @staticmethod
    def by_has_integration_id(has_integration: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if has_integration:
                return DomainRow.integration_id.is_not(None)
            return DomainRow.integration_id.is_(None)

        return inner

    # ==================== DateTime Filters ====================

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        """Filter by created_at < datetime."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        """Filter by created_at > datetime."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.created_at > dt

        return inner

    @staticmethod
    def by_modified_at_before(dt: datetime) -> QueryCondition:
        """Filter by modified_at < datetime."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.modified_at < dt

        return inner

    @staticmethod
    def by_modified_at_after(dt: datetime) -> QueryCondition:
        """Filter by modified_at > datetime."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.modified_at > dt

        return inner

    # ==================== Resource Group Filters ====================

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        """Filter domains by resource group (scaling group).

        This requires joining with the sgroups_for_domains table.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.exists(
                sa.select(1)
                .where(ScalingGroupForDomainRow.domain == DomainRow.name)
                .where(ScalingGroupForDomainRow.scaling_group == resource_group)
            )

        return inner

    # ==================== Cursor Pagination ====================

    @staticmethod
    def by_cursor_forward(cursor_name: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DomainRow.created_at)
                .where(DomainRow.name == cursor_name)
                .scalar_subquery()
            )
            return DomainRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_name: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DomainRow.created_at)
                .where(DomainRow.name == cursor_name)
                .scalar_subquery()
            )
            return DomainRow.created_at > subquery

        return inner

    # ==================== Project Nested Filters ====================

    @staticmethod
    def _exists_project(
        *project_conditions: sa.sql.expression.ColumnElement[bool],
    ) -> sa.sql.expression.ColumnElement[bool]:
        """EXISTS subquery: Domain → Project (via FK GroupRow.domain_name)."""
        subq = sa.select(sa.literal(1)).where(GroupRow.domain_name == DomainRow.name)
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
            return DomainConditions._exists_project(cond)

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
            return DomainConditions._exists_project(cond)

        return inner

    @staticmethod
    def by_project_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainConditions._exists_project(GroupRow.is_active == is_active)

        return inner

    @staticmethod
    def exists_project_combined(project_conditions: list[QueryCondition]) -> QueryCondition:
        """Combine multiple project conditions into single EXISTS subquery."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(GroupRow.domain_name == DomainRow.name)
            for cond in project_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner

    # ==================== User Nested Filters ====================

    @staticmethod
    def _exists_user(
        *user_conditions: sa.sql.expression.ColumnElement[bool],
    ) -> sa.sql.expression.ColumnElement[bool]:
        """EXISTS subquery: Domain → User (via FK UserRow.domain_name)."""
        subq = sa.select(sa.literal(1)).where(UserRow.domain_name == DomainRow.name)
        for cond in user_conditions:
            subq = subq.where(cond)
        return sa.exists(subq)

    @staticmethod
    def by_user_username_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = UserRow.username.ilike(f"%{spec.value}%")
            else:
                cond = UserRow.username.like(f"%{spec.value}%")
            if spec.negated:
                cond = sa.not_(cond)
            return DomainConditions._exists_user(cond)

        return inner

    @staticmethod
    def by_user_username_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = sa.func.lower(UserRow.username) == spec.value.lower()
            else:
                cond = UserRow.username == spec.value
            if spec.negated:
                cond = sa.not_(cond)
            return DomainConditions._exists_user(cond)

        return inner

    @staticmethod
    def by_user_email_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = UserRow.email.ilike(f"%{spec.value}%")
            else:
                cond = UserRow.email.like(f"%{spec.value}%")
            if spec.negated:
                cond = sa.not_(cond)
            return DomainConditions._exists_user(cond)

        return inner

    @staticmethod
    def by_user_email_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                cond = sa.func.lower(UserRow.email) == spec.value.lower()
            else:
                cond = UserRow.email == spec.value
            if spec.negated:
                cond = sa.not_(cond)
            return DomainConditions._exists_user(cond)

        return inner

    @staticmethod
    def by_user_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if is_active:
                return DomainConditions._exists_user(UserRow.status == UserStatus.ACTIVE)
            return DomainConditions._exists_user(UserRow.status != UserStatus.ACTIVE)

        return inner

    @staticmethod
    def exists_user_combined(user_conditions: list[QueryCondition]) -> QueryCondition:
        """Combine multiple user conditions into single EXISTS subquery."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(UserRow.domain_name == DomainRow.name)
            for cond in user_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner


class DomainOrders:
    """Query orders for sorting domains."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.name.asc()
        return DomainRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.created_at.asc()
        return DomainRow.created_at.desc()

    @staticmethod
    def modified_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.modified_at.asc()
        return DomainRow.modified_at.desc()

    @staticmethod
    def is_active(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.is_active.asc()
        return DomainRow.is_active.desc()

    # ==================== Project Nested Orders ====================

    @staticmethod
    def _scalar_project_min(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        """Scalar subquery with MIN for 1:N relationship (Domain → Project)."""
        return (
            sa.select(sa.func.min(column))
            .where(GroupRow.domain_name == DomainRow.name)
            .correlate(DomainRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_project_name(ascending: bool = True) -> QueryOrder:
        subq = DomainOrders._scalar_project_min(GroupRow.name)
        return subq.asc() if ascending else subq.desc()

    # ==================== User Nested Orders ====================

    @staticmethod
    def _scalar_user_min(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        """Scalar subquery with MIN for 1:N relationship (Domain → User)."""
        return (
            sa.select(sa.func.min(column))
            .where(UserRow.domain_name == DomainRow.name)
            .correlate(DomainRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_user_username(ascending: bool = True) -> QueryOrder:
        subq = DomainOrders._scalar_user_min(UserRow.username)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_user_email(ascending: bool = True) -> QueryOrder:
        subq = DomainOrders._scalar_user_min(UserRow.email)
        return subq.asc() if ascending else subq.desc()

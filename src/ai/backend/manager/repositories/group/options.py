"""Query conditions and orders for group repository operations."""

from __future__ import annotations

from collections.abc import Collection
from datetime import datetime
from typing import Any
from uuid import UUID

import sqlalchemy as sa

from ai.backend.manager.api.gql.base import StringMatchSpec, UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder

__all__ = (
    "GroupConditions",
    "GroupOrders",
)


class GroupConditions:
    """Query conditions for filtering groups/projects."""

    # ==================== Name Filters ====================

    @staticmethod
    def by_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = GroupRow.name.ilike(f"%{spec.value}%")
            else:
                condition = GroupRow.name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(GroupRow.name) == spec.value.lower()
            else:
                condition = GroupRow.name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = GroupRow.name.ilike(f"{spec.value}%")
            else:
                condition = GroupRow.name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = GroupRow.name.ilike(f"%{spec.value}")
            else:
                condition = GroupRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ==================== Domain Name Filters ====================

    @staticmethod
    def by_domain_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = GroupRow.domain_name.ilike(f"%{spec.value}%")
            else:
                condition = GroupRow.domain_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(GroupRow.domain_name) == spec.value.lower()
            else:
                condition = GroupRow.domain_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = GroupRow.domain_name.ilike(f"{spec.value}%")
            else:
                condition = GroupRow.domain_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = GroupRow.domain_name.ilike(f"%{spec.value}")
            else:
                condition = GroupRow.domain_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ==================== Type Filters ====================

    @staticmethod
    def by_type_equals(project_type: ProjectType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.type == project_type

        return inner

    @staticmethod
    def by_type_in(types: Collection[ProjectType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.type.in_(types)

        return inner

    # ==================== Active Status Filters ====================

    @staticmethod
    def by_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.is_active == is_active

        return inner

    # ==================== ID (UUID) Filters ====================

    @staticmethod
    def by_id_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        """Filter by project ID equality.

        Args:
            spec: UUID equality specification with value and negated flag.

        Returns:
            QueryCondition callable for project ID filtering.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = GroupRow.id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        """Filter by project ID IN operation.

        Args:
            spec: UUID IN specification with values list and negated flag.

        Returns:
            QueryCondition callable for project ID IN filtering.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = GroupRow.id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    # ==================== DateTime Filters ====================

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        """Filter by created_at < datetime."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.created_at < dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        """Filter by created_at > datetime."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.created_at > dt

        return inner

    @staticmethod
    def by_modified_at_before(dt: datetime) -> QueryCondition:
        """Filter by modified_at < datetime."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.modified_at < dt

        return inner

    @staticmethod
    def by_modified_at_after(dt: datetime) -> QueryCondition:
        """Filter by modified_at > datetime."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.modified_at > dt

        return inner

    # ==================== Cursor Pagination ====================

    @staticmethod
    def by_cursor_forward(cursor_id: UUID) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(GroupRow.created_at).where(GroupRow.id == cursor_id).scalar_subquery()
            )
            return GroupRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: UUID) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(GroupRow.created_at).where(GroupRow.id == cursor_id).scalar_subquery()
            )
            return GroupRow.created_at > subquery

        return inner

    # ==================== Domain Nested Filters ====================

    @staticmethod
    def _exists_domain(
        *domain_conditions: sa.sql.expression.ColumnElement[bool],
    ) -> sa.sql.expression.ColumnElement[bool]:
        """EXISTS subquery: Group → Domain with given conditions."""
        subq = sa.select(sa.literal(1)).where(DomainRow.name == GroupRow.domain_name)
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
            return GroupConditions._exists_domain(cond)

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
            return GroupConditions._exists_domain(cond)

        return inner

    @staticmethod
    def by_domain_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupConditions._exists_domain(DomainRow.is_active == is_active)

        return inner

    @staticmethod
    def exists_domain_combined(domain_conditions: list[QueryCondition]) -> QueryCondition:
        """Combine multiple domain conditions into single EXISTS subquery.

        Accepts conditions from DomainV2Filter.build_conditions() directly.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subq = sa.select(sa.literal(1)).where(DomainRow.name == GroupRow.domain_name)
            for cond in domain_conditions:
                subq = subq.where(cond())
            return sa.exists(subq)

        return inner


class GroupOrders:
    """Query orders for sorting groups/projects."""

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.id.asc()
        return GroupRow.id.desc()

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.name.asc()
        return GroupRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.created_at.asc()
        return GroupRow.created_at.desc()

    @staticmethod
    def modified_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.modified_at.asc()
        return GroupRow.modified_at.desc()

    @staticmethod
    def domain_name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.domain_name.asc()
        return GroupRow.domain_name.desc()

    @staticmethod
    def type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.type.asc()
        return GroupRow.type.desc()

    # ==================== Domain Nested Orders ====================

    @staticmethod
    def _scalar_domain(
        column: sa.ColumnElement[Any] | sa.orm.InstrumentedAttribute[Any],
    ) -> sa.ScalarSelect[Any]:
        """Scalar subquery selecting a Domain column correlated to current Group."""
        return (
            sa.select(column)
            .where(DomainRow.name == GroupRow.domain_name)
            .correlate(GroupRow)
            .scalar_subquery()
        )

    @staticmethod
    def by_domain_name(ascending: bool = True) -> QueryOrder:
        subq = GroupOrders._scalar_domain(DomainRow.name)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_domain_is_active(ascending: bool = True) -> QueryOrder:
        subq = GroupOrders._scalar_domain(DomainRow.is_active)
        return subq.asc() if ascending else subq.desc()

    @staticmethod
    def by_domain_created_at(ascending: bool = True) -> QueryOrder:
        subq = GroupOrders._scalar_domain(DomainRow.created_at)
        return subq.asc() if ascending else subq.desc()

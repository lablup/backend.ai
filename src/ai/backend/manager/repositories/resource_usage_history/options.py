"""Query conditions and orders for Resource Usage History repository."""

from __future__ import annotations

import uuid
from datetime import date, datetime

import sqlalchemy as sa

from ai.backend.manager.models.resource_usage_history import (
    DomainUsageBucketRow,
    KernelUsageRecordRow,
    ProjectUsageBucketRow,
    UserUsageBucketRow,
)
from ai.backend.manager.repositories.base.types import QueryCondition, QueryOrder


class KernelUsageRecordConditions:
    """Query conditions for KernelUsageRecordRow."""

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelUsageRecordRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_kernel_id(kernel_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelUsageRecordRow.kernel_id == kernel_id

        return inner

    @staticmethod
    def by_session_id(session_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelUsageRecordRow.session_id == session_id

        return inner

    @staticmethod
    def by_user_uuid(user_uuid: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelUsageRecordRow.user_uuid == user_uuid

        return inner

    @staticmethod
    def by_project_id(project_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return KernelUsageRecordRow.project_id == project_id

        return inner

    @staticmethod
    def by_period_range(start: datetime, end: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                KernelUsageRecordRow.period_start >= start,
                KernelUsageRecordRow.period_end <= end,
            )

        return inner


class KernelUsageRecordOrders:
    """Query orders for KernelUsageRecordRow."""

    @staticmethod
    def by_period_start(ascending: bool = True) -> QueryOrder:
        col = KernelUsageRecordRow.period_start
        return col.asc() if ascending else col.desc()


class DomainUsageBucketConditions:
    """Query conditions for DomainUsageBucketRow."""

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_resource_group_contains(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.resource_group.like(f"%{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_equals(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_starts_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.resource_group.like(f"{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_ends_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.resource_group.like(f"%{resource_group}")

        return inner

    @staticmethod
    def by_domain_name_contains(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.domain_name.like(f"%{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_equals(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_domain_name_starts_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.domain_name.like(f"{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_ends_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.domain_name.like(f"%{domain_name}")

        return inner

    @staticmethod
    def by_period_range(start: date, end: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                DomainUsageBucketRow.period_start >= start,
                DomainUsageBucketRow.period_start <= end,
            )

        return inner

    @staticmethod
    def by_period_start(period_start: date) -> QueryCondition:
        """Filter by exact period start date."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.period_start == period_start

        return inner

    @staticmethod
    def by_period_start_not_equals(period_start: date) -> QueryCondition:
        """Filter by period start date not equal to the given value."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.period_start != period_start

        return inner

    @staticmethod
    def by_period_start_before(before: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.period_start < before

        return inner

    @staticmethod
    def by_period_start_after(after: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.period_start > after

        return inner

    @staticmethod
    def by_period_end(period_end: date) -> QueryCondition:
        """Filter by exact period end date."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.period_end == period_end

        return inner

    @staticmethod
    def by_period_end_not_equals(period_end: date) -> QueryCondition:
        """Filter by period end date not equal to the given value."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.period_end != period_end

        return inner

    @staticmethod
    def by_period_end_before(before: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.period_end < before

        return inner

    @staticmethod
    def by_period_end_after(after: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainUsageBucketRow.period_end > after

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get period_start of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DomainUsageBucketRow.period_start)
                .where(DomainUsageBucketRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return DomainUsageBucketRow.period_start < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get period_start of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DomainUsageBucketRow.period_start)
                .where(DomainUsageBucketRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return DomainUsageBucketRow.period_start > subquery

        return inner


class DomainUsageBucketOrders:
    """Query orders for DomainUsageBucketRow."""

    @staticmethod
    def by_period_start(ascending: bool = True) -> QueryOrder:
        col = DomainUsageBucketRow.period_start
        return col.asc() if ascending else col.desc()


class ProjectUsageBucketConditions:
    """Query conditions for ProjectUsageBucketRow."""

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_resource_group_contains(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.resource_group.like(f"%{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_equals(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_starts_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.resource_group.like(f"{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_ends_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.resource_group.like(f"%{resource_group}")

        return inner

    @staticmethod
    def by_domain_name_contains(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.domain_name.like(f"%{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_equals(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_domain_name_starts_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.domain_name.like(f"{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_ends_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.domain_name.like(f"%{domain_name}")

        return inner

    @staticmethod
    def by_project_id(project_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.project_id == project_id

        return inner

    @staticmethod
    def by_period_range(start: date, end: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                ProjectUsageBucketRow.period_start >= start,
                ProjectUsageBucketRow.period_start <= end,
            )

        return inner

    @staticmethod
    def by_period_start(period_start: date) -> QueryCondition:
        """Filter by exact period start date."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.period_start == period_start

        return inner

    @staticmethod
    def by_period_start_not_equals(period_start: date) -> QueryCondition:
        """Filter by period start date not equal to the given value."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.period_start != period_start

        return inner

    @staticmethod
    def by_period_start_before(before: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.period_start < before

        return inner

    @staticmethod
    def by_period_start_after(after: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.period_start > after

        return inner

    @staticmethod
    def by_period_end(period_end: date) -> QueryCondition:
        """Filter by exact period end date."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.period_end == period_end

        return inner

    @staticmethod
    def by_period_end_not_equals(period_end: date) -> QueryCondition:
        """Filter by period end date not equal to the given value."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.period_end != period_end

        return inner

    @staticmethod
    def by_period_end_before(before: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.period_end < before

        return inner

    @staticmethod
    def by_period_end_after(after: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectUsageBucketRow.period_end > after

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get period_start of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ProjectUsageBucketRow.period_start)
                .where(ProjectUsageBucketRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return ProjectUsageBucketRow.period_start < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get period_start of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ProjectUsageBucketRow.period_start)
                .where(ProjectUsageBucketRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return ProjectUsageBucketRow.period_start > subquery

        return inner


class ProjectUsageBucketOrders:
    """Query orders for ProjectUsageBucketRow."""

    @staticmethod
    def by_period_start(ascending: bool = True) -> QueryOrder:
        col = ProjectUsageBucketRow.period_start
        return col.asc() if ascending else col.desc()


class UserUsageBucketConditions:
    """Query conditions for UserUsageBucketRow."""

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_resource_group_contains(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.resource_group.like(f"%{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_equals(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_starts_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.resource_group.like(f"{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_ends_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.resource_group.like(f"%{resource_group}")

        return inner

    @staticmethod
    def by_domain_name_contains(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.domain_name.like(f"%{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_equals(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_domain_name_starts_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.domain_name.like(f"{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_ends_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.domain_name.like(f"%{domain_name}")

        return inner

    @staticmethod
    def by_user_uuid(user_uuid: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.user_uuid == user_uuid

        return inner

    @staticmethod
    def by_project_id(project_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.project_id == project_id

        return inner

    @staticmethod
    def by_period_range(start: date, end: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return sa.and_(
                UserUsageBucketRow.period_start >= start,
                UserUsageBucketRow.period_start <= end,
            )

        return inner

    @staticmethod
    def by_period_start(period_start: date) -> QueryCondition:
        """Filter by exact period start date."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.period_start == period_start

        return inner

    @staticmethod
    def by_period_start_not_equals(period_start: date) -> QueryCondition:
        """Filter by period start date not equal to the given value."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.period_start != period_start

        return inner

    @staticmethod
    def by_period_start_before(before: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.period_start < before

        return inner

    @staticmethod
    def by_period_start_after(after: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.period_start > after

        return inner

    @staticmethod
    def by_period_end(period_end: date) -> QueryCondition:
        """Filter by exact period end date."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.period_end == period_end

        return inner

    @staticmethod
    def by_period_end_not_equals(period_end: date) -> QueryCondition:
        """Filter by period end date not equal to the given value."""

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.period_end != period_end

        return inner

    @staticmethod
    def by_period_end_before(before: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.period_end < before

        return inner

    @staticmethod
    def by_period_end_after(after: date) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserUsageBucketRow.period_end > after

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get period_start of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(UserUsageBucketRow.period_start)
                .where(UserUsageBucketRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return UserUsageBucketRow.period_start < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get period_start of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(UserUsageBucketRow.period_start)
                .where(UserUsageBucketRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return UserUsageBucketRow.period_start > subquery

        return inner


class UserUsageBucketOrders:
    """Query orders for UserUsageBucketRow."""

    @staticmethod
    def by_period_start(ascending: bool = True) -> QueryOrder:
        col = UserUsageBucketRow.period_start
        return col.asc() if ascending else col.desc()

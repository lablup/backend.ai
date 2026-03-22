"""Query conditions and orders for Fair Share repository."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.data.filter_specs import StringMatchSpec, UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base.types import QueryCondition, QueryOrder


class DomainFairShareConditions:
    """Query conditions for DomainFairShareRow."""

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainFairShareRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainFairShareRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_resource_group_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainFairShareRow.resource_group.ilike(f"%{spec.value}%")
            else:
                condition = DomainFairShareRow.resource_group.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(DomainFairShareRow.resource_group) == spec.value.lower()
            else:
                condition = DomainFairShareRow.resource_group == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainFairShareRow.resource_group.ilike(f"{spec.value}%")
            else:
                condition = DomainFairShareRow.resource_group.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainFairShareRow.resource_group.ilike(f"%{spec.value}")
            else:
                condition = DomainFairShareRow.resource_group.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainFairShareRow.domain_name.ilike(f"%{spec.value}%")
            else:
                condition = DomainFairShareRow.domain_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(DomainFairShareRow.domain_name) == spec.value.lower()
            else:
                condition = DomainFairShareRow.domain_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainFairShareRow.domain_name.ilike(f"{spec.value}%")
            else:
                condition = DomainFairShareRow.domain_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainFairShareRow.domain_name.ilike(f"%{spec.value}")
            else:
                condition = DomainFairShareRow.domain_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DomainFairShareRow.created_at)
                .where(DomainFairShareRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return DomainFairShareRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(DomainFairShareRow.created_at)
                .where(DomainFairShareRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return DomainFairShareRow.created_at > subquery

        return inner

    @staticmethod
    def by_domain_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.is_active == is_active

        return inner


class DomainFairShareOrders:
    """Query orders for DomainFairShareRow."""

    @staticmethod
    def by_fair_share_factor(ascending: bool = False) -> QueryOrder:
        col = DomainFairShareRow.fair_share_factor
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_domain_name(ascending: bool = True) -> QueryOrder:
        col = DomainFairShareRow.domain_name
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = DomainFairShareRow.created_at
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_domain_is_active(ascending: bool = True) -> QueryOrder:
        col = DomainRow.is_active
        return col.asc() if ascending else col.desc()


class ProjectFairShareConditions:
    """Query conditions for ProjectFairShareRow."""

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_project_id(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = ProjectFairShareRow.project_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_project_ids(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = ProjectFairShareRow.project_id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_resource_group_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ProjectFairShareRow.resource_group.ilike(f"%{spec.value}%")
            else:
                condition = ProjectFairShareRow.resource_group.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ProjectFairShareRow.resource_group) == spec.value.lower()
            else:
                condition = ProjectFairShareRow.resource_group == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ProjectFairShareRow.resource_group.ilike(f"{spec.value}%")
            else:
                condition = ProjectFairShareRow.resource_group.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ProjectFairShareRow.resource_group.ilike(f"%{spec.value}")
            else:
                condition = ProjectFairShareRow.resource_group.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ProjectFairShareRow.domain_name.ilike(f"%{spec.value}%")
            else:
                condition = ProjectFairShareRow.domain_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ProjectFairShareRow.domain_name) == spec.value.lower()
            else:
                condition = ProjectFairShareRow.domain_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ProjectFairShareRow.domain_name.ilike(f"{spec.value}%")
            else:
                condition = ProjectFairShareRow.domain_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ProjectFairShareRow.domain_name.ilike(f"%{spec.value}")
            else:
                condition = ProjectFairShareRow.domain_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ProjectFairShareRow.created_at)
                .where(ProjectFairShareRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return ProjectFairShareRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(ProjectFairShareRow.created_at)
                .where(ProjectFairShareRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return ProjectFairShareRow.created_at > subquery

        return inner

    @staticmethod
    def by_project_name_contains(spec: StringMatchSpec) -> QueryCondition:
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
    def by_project_name_equals(spec: StringMatchSpec) -> QueryCondition:
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
    def by_project_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
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
    def by_project_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = GroupRow.name.ilike(f"%{spec.value}")
            else:
                condition = GroupRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_project_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.is_active == is_active

        return inner

    @staticmethod
    def by_project_type_equals(project_type: ProjectType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.type == project_type

        return inner

    @staticmethod
    def by_project_type_in(project_types: Collection[ProjectType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.type.in_(project_types)

        return inner


class ProjectFairShareOrders:
    """Query orders for ProjectFairShareRow."""

    @staticmethod
    def by_fair_share_factor(ascending: bool = False) -> QueryOrder:
        col = ProjectFairShareRow.fair_share_factor
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = ProjectFairShareRow.created_at
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_project_name(ascending: bool = True) -> QueryOrder:
        col = GroupRow.name
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_project_is_active(ascending: bool = True) -> QueryOrder:
        col = GroupRow.is_active
        return col.asc() if ascending else col.desc()


class UserFairShareConditions:
    """Query conditions for UserFairShareRow."""

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_user_uuid(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = UserFairShareRow.user_uuid == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_project_id(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = UserFairShareRow.project_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_user_uuids(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = UserFairShareRow.user_uuid.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_project_ids(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = UserFairShareRow.project_id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_resource_group_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserFairShareRow.resource_group.ilike(f"%{spec.value}%")
            else:
                condition = UserFairShareRow.resource_group.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(UserFairShareRow.resource_group) == spec.value.lower()
            else:
                condition = UserFairShareRow.resource_group == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserFairShareRow.resource_group.ilike(f"{spec.value}%")
            else:
                condition = UserFairShareRow.resource_group.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserFairShareRow.resource_group.ilike(f"%{spec.value}")
            else:
                condition = UserFairShareRow.resource_group.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserFairShareRow.domain_name.ilike(f"%{spec.value}%")
            else:
                condition = UserFairShareRow.domain_name.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(UserFairShareRow.domain_name) == spec.value.lower()
            else:
                condition = UserFairShareRow.domain_name == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserFairShareRow.domain_name.ilike(f"{spec.value}%")
            else:
                condition = UserFairShareRow.domain_name.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserFairShareRow.domain_name.ilike(f"%{spec.value}")
            else:
                condition = UserFairShareRow.domain_name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(UserFairShareRow.created_at)
                .where(UserFairShareRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return UserFairShareRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(UserFairShareRow.created_at)
                .where(UserFairShareRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return UserFairShareRow.created_at > subquery

        return inner

    @staticmethod
    def by_user_username_contains(spec: StringMatchSpec) -> QueryCondition:
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
    def by_user_username_equals(spec: StringMatchSpec) -> QueryCondition:
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
    def by_user_username_starts_with(spec: StringMatchSpec) -> QueryCondition:
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
    def by_user_username_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.username.ilike(f"%{spec.value}")
            else:
                condition = UserRow.username.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_user_email_contains(spec: StringMatchSpec) -> QueryCondition:
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
    def by_user_email_equals(spec: StringMatchSpec) -> QueryCondition:
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
    def by_user_email_starts_with(spec: StringMatchSpec) -> QueryCondition:
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
    def by_user_email_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserRow.email.ilike(f"%{spec.value}")
            else:
                condition = UserRow.email.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_user_is_active(is_active: bool) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if is_active:
                return UserRow.status == UserStatus.ACTIVE
            return UserRow.status != UserStatus.ACTIVE

        return inner


class UserFairShareOrders:
    """Query orders for UserFairShareRow."""

    @staticmethod
    def by_fair_share_factor(ascending: bool = False) -> QueryOrder:
        col = UserFairShareRow.fair_share_factor
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = UserFairShareRow.created_at
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_user_username(ascending: bool = True) -> QueryOrder:
        col = UserRow.username
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_user_email(ascending: bool = True) -> QueryOrder:
        col = UserRow.email
        return col.asc() if ascending else col.desc()


# ==================== RG-context conditions ====================
# These condition classes reference INNER JOIN'd columns instead of
# LEFT JOIN'd FairShareRow columns, so they work correctly in
# search_rg_* queries where FairShareRow columns can be NULL for
# entities without fair share records.


class RGDomainFairShareConditions:
    """Query conditions for rg-scoped domain fair share queries.

    References DomainRow (base table) for domain_name conditions and
    DomainFairShareRow (LEFT JOIN'd) for resource_group conditions.
    """

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name == domain_name

        return inner

    @staticmethod
    def by_domain_name_contains(spec: StringMatchSpec) -> QueryCondition:
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
    def by_domain_name_equals(spec: StringMatchSpec) -> QueryCondition:
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
    def by_domain_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
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
    def by_domain_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.name.ilike(f"%{spec.value}")
            else:
                condition = DomainRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainFairShareRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainFairShareRow.resource_group.ilike(f"%{spec.value}%")
            else:
                condition = DomainFairShareRow.resource_group.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(DomainFairShareRow.resource_group) == spec.value.lower()
            else:
                condition = DomainFairShareRow.resource_group == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainFairShareRow.resource_group.ilike(f"{spec.value}%")
            else:
                condition = DomainFairShareRow.resource_group.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainFairShareRow.resource_group.ilike(f"%{spec.value}")
            else:
                condition = DomainFairShareRow.resource_group.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner


class RGDomainFairShareOrders:
    """Query orders for rg-scoped domain fair share queries.

    Uses DomainRow (base table) columns for reliable sorting,
    and DomainFairShareRow (LEFT JOIN'd) for fair-share-specific ordering.
    """

    @staticmethod
    def by_domain_name(ascending: bool = True) -> QueryOrder:
        col = DomainRow.name
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_fair_share_factor(ascending: bool = False) -> QueryOrder:
        col = DomainFairShareRow.fair_share_factor
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = DomainFairShareRow.created_at
        return col.asc() if ascending else col.desc()


class RGProjectFairShareConditions:
    """Query conditions for rg-scoped project fair share queries.

    References GroupRow (base table) for project conditions, DomainRow (INNER JOIN'd)
    for domain conditions, and ProjectFairShareRow (LEFT JOIN'd) for resource_group conditions.
    """

    @staticmethod
    def by_project_id(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = GroupRow.id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_project_ids(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = GroupRow.id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name == domain_name

        return inner

    @staticmethod
    def by_domain_name_contains(spec: StringMatchSpec) -> QueryCondition:
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
    def by_domain_name_equals(spec: StringMatchSpec) -> QueryCondition:
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
    def by_domain_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
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
    def by_domain_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.name.ilike(f"%{spec.value}")
            else:
                condition = DomainRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ProjectFairShareRow.resource_group.ilike(f"%{spec.value}%")
            else:
                condition = ProjectFairShareRow.resource_group.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(ProjectFairShareRow.resource_group) == spec.value.lower()
            else:
                condition = ProjectFairShareRow.resource_group == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ProjectFairShareRow.resource_group.ilike(f"{spec.value}%")
            else:
                condition = ProjectFairShareRow.resource_group.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = ProjectFairShareRow.resource_group.ilike(f"%{spec.value}")
            else:
                condition = ProjectFairShareRow.resource_group.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner


class RGProjectFairShareOrders:
    """Query orders for rg-scoped project fair share queries.

    Uses ProjectFairShareRow (LEFT JOIN'd) for fair-share-specific ordering.
    """

    @staticmethod
    def by_fair_share_factor(ascending: bool = False) -> QueryOrder:
        col = ProjectFairShareRow.fair_share_factor
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = ProjectFairShareRow.created_at
        return col.asc() if ascending else col.desc()


class RGUserFairShareConditions:
    """Query conditions for rg-scoped user fair share queries.

    References AssocGroupUserRow (base table), GroupRow/DomainRow/UserRow (INNER JOIN'd),
    and UserFairShareRow (LEFT JOIN'd) for resource_group conditions.
    """

    @staticmethod
    def by_user_uuid(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = AssocGroupUserRow.user_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_user_uuids(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = AssocGroupUserRow.user_id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_project_id(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = AssocGroupUserRow.group_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_project_ids(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = AssocGroupUserRow.group_id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name == domain_name

        return inner

    @staticmethod
    def by_domain_name_contains(spec: StringMatchSpec) -> QueryCondition:
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
    def by_domain_name_equals(spec: StringMatchSpec) -> QueryCondition:
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
    def by_domain_name_starts_with(spec: StringMatchSpec) -> QueryCondition:
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
    def by_domain_name_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = DomainRow.name.ilike(f"%{spec.value}")
            else:
                condition = DomainRow.name.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_contains(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserFairShareRow.resource_group.ilike(f"%{spec.value}%")
            else:
                condition = UserFairShareRow.resource_group.like(f"%{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_equals(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = sa.func.lower(UserFairShareRow.resource_group) == spec.value.lower()
            else:
                condition = UserFairShareRow.resource_group == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_starts_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserFairShareRow.resource_group.ilike(f"{spec.value}%")
            else:
                condition = UserFairShareRow.resource_group.like(f"{spec.value}%")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_resource_group_ends_with(spec: StringMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if spec.case_insensitive:
                condition = UserFairShareRow.resource_group.ilike(f"%{spec.value}")
            else:
                condition = UserFairShareRow.resource_group.like(f"%{spec.value}")
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner


class RGUserFairShareOrders:
    """Query orders for rg-scoped user fair share queries.

    Uses UserFairShareRow (LEFT JOIN'd) for fair-share-specific ordering.
    """

    @staticmethod
    def by_fair_share_factor(ascending: bool = False) -> QueryOrder:
        col = UserFairShareRow.fair_share_factor
        return col.asc() if ascending else col.desc()

    @staticmethod
    def by_created_at(ascending: bool = True) -> QueryOrder:
        col = UserFairShareRow.created_at
        return col.asc() if ascending else col.desc()

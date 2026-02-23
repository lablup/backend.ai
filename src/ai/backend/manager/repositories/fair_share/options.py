"""Query conditions and orders for Fair Share repository."""

from __future__ import annotations

import uuid
from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.manager.data.group.types import ProjectType
from ai.backend.manager.data.user.types import UserStatus
from ai.backend.manager.models.domain import DomainRow
from ai.backend.manager.models.fair_share import (
    DomainFairShareRow,
    ProjectFairShareRow,
    UserFairShareRow,
)
from ai.backend.manager.models.group import AssocGroupUserRow, GroupRow
from ai.backend.manager.models.scaling_group import (
    ScalingGroupForDomainRow,
    ScalingGroupForProjectRow,
)
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
    def by_resource_group_contains(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainFairShareRow.resource_group.like(f"%{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_equals(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainFairShareRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_starts_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainFairShareRow.resource_group.like(f"{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_ends_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainFairShareRow.resource_group.like(f"%{resource_group}")

        return inner

    @staticmethod
    def by_domain_name_contains(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainFairShareRow.domain_name.like(f"%{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_equals(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainFairShareRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_domain_name_starts_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainFairShareRow.domain_name.like(f"{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_ends_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainFairShareRow.domain_name.like(f"%{domain_name}")

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
    def by_project_id(project_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.project_id == project_id

        return inner

    @staticmethod
    def by_project_ids(project_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.project_id.in_(project_ids)

        return inner

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_resource_group_contains(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.resource_group.like(f"%{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_equals(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_starts_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.resource_group.like(f"{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_ends_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.resource_group.like(f"%{resource_group}")

        return inner

    @staticmethod
    def by_domain_name_contains(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.domain_name.like(f"%{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_equals(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_domain_name_starts_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.domain_name.like(f"{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_ends_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ProjectFairShareRow.domain_name.like(f"%{domain_name}")

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
    def by_project_name_contains(name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.name.like(f"%{name}%")

        return inner

    @staticmethod
    def by_project_name_equals(name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.name == name

        return inner

    @staticmethod
    def by_project_name_starts_with(name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.name.like(f"{name}%")

        return inner

    @staticmethod
    def by_project_name_ends_with(name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return GroupRow.name.like(f"%{name}")

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
    def by_user_uuid(user_uuid: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.user_uuid == user_uuid

        return inner

    @staticmethod
    def by_project_id(project_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.project_id == project_id

        return inner

    @staticmethod
    def by_user_uuids(user_uuids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.user_uuid.in_(user_uuids)

        return inner

    @staticmethod
    def by_project_ids(project_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.project_id.in_(project_ids)

        return inner

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_resource_group_contains(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.resource_group.like(f"%{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_equals(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.resource_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_starts_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.resource_group.like(f"{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_ends_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.resource_group.like(f"%{resource_group}")

        return inner

    @staticmethod
    def by_domain_name_contains(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.domain_name.like(f"%{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_equals(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.domain_name == domain_name

        return inner

    @staticmethod
    def by_domain_name_starts_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.domain_name.like(f"{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_ends_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserFairShareRow.domain_name.like(f"%{domain_name}")

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
    def by_user_username_contains(username: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.username.like(f"%{username}%")

        return inner

    @staticmethod
    def by_user_username_equals(username: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.username == username

        return inner

    @staticmethod
    def by_user_username_starts_with(username: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.username.like(f"{username}%")

        return inner

    @staticmethod
    def by_user_username_ends_with(username: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.username.like(f"%{username}")

        return inner

    @staticmethod
    def by_user_email_contains(email: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.email.like(f"%{email}%")

        return inner

    @staticmethod
    def by_user_email_equals(email: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.email == email

        return inner

    @staticmethod
    def by_user_email_starts_with(email: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.email.like(f"{email}%")

        return inner

    @staticmethod
    def by_user_email_ends_with(email: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRow.email.like(f"%{email}")

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

    References ScalingGroupForDomainRow (INNER JOIN'd base table)
    instead of DomainFairShareRow (LEFT JOIN'd).
    """

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForDomainRow.domain == domain_name

        return inner

    @staticmethod
    def by_domain_name_contains(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForDomainRow.domain.like(f"%{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_equals(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForDomainRow.domain == domain_name

        return inner

    @staticmethod
    def by_domain_name_starts_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForDomainRow.domain.like(f"{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_ends_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForDomainRow.domain.like(f"%{domain_name}")

        return inner

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForDomainRow.scaling_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_contains(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForDomainRow.scaling_group.like(f"%{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_equals(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForDomainRow.scaling_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_starts_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForDomainRow.scaling_group.like(f"{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_ends_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForDomainRow.scaling_group.like(f"%{resource_group}")

        return inner


class RGDomainFairShareOrders:
    """Query orders for rg-scoped domain fair share queries.

    Uses INNER JOIN'd columns where available to avoid NULL sorting issues.
    """

    @staticmethod
    def by_domain_name(ascending: bool = True) -> QueryOrder:
        col = ScalingGroupForDomainRow.domain
        return col.asc() if ascending else col.desc()


class RGProjectFairShareConditions:
    """Query conditions for rg-scoped project fair share queries.

    References ScalingGroupForProjectRow/GroupRow/DomainRow (INNER JOIN'd)
    instead of ProjectFairShareRow (LEFT JOIN'd).
    """

    @staticmethod
    def by_project_id(project_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForProjectRow.group == project_id

        return inner

    @staticmethod
    def by_project_ids(project_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForProjectRow.group.in_(project_ids)

        return inner

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name == domain_name

        return inner

    @staticmethod
    def by_domain_name_contains(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name.like(f"%{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_equals(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name == domain_name

        return inner

    @staticmethod
    def by_domain_name_starts_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name.like(f"{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_ends_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name.like(f"%{domain_name}")

        return inner

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForProjectRow.scaling_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_contains(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForProjectRow.scaling_group.like(f"%{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_equals(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForProjectRow.scaling_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_starts_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForProjectRow.scaling_group.like(f"{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_ends_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForProjectRow.scaling_group.like(f"%{resource_group}")

        return inner


class RGUserFairShareConditions:
    """Query conditions for rg-scoped user fair share queries.

    References AssocGroupUserRow/DomainRow/ScalingGroupForProjectRow (INNER JOIN'd)
    instead of UserFairShareRow (LEFT JOIN'd).
    """

    @staticmethod
    def by_user_uuid(user_uuid: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AssocGroupUserRow.user_id == user_uuid

        return inner

    @staticmethod
    def by_user_uuids(user_uuids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AssocGroupUserRow.user_id.in_(user_uuids)

        return inner

    @staticmethod
    def by_project_id(project_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AssocGroupUserRow.group_id == project_id

        return inner

    @staticmethod
    def by_project_ids(project_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return AssocGroupUserRow.group_id.in_(project_ids)

        return inner

    @staticmethod
    def by_domain_name(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name == domain_name

        return inner

    @staticmethod
    def by_domain_name_contains(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name.like(f"%{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_equals(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name == domain_name

        return inner

    @staticmethod
    def by_domain_name_starts_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name.like(f"{domain_name}%")

        return inner

    @staticmethod
    def by_domain_name_ends_with(domain_name: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return DomainRow.name.like(f"%{domain_name}")

        return inner

    @staticmethod
    def by_resource_group(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForProjectRow.scaling_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_contains(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForProjectRow.scaling_group.like(f"%{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_equals(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForProjectRow.scaling_group == resource_group

        return inner

    @staticmethod
    def by_resource_group_starts_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForProjectRow.scaling_group.like(f"{resource_group}%")

        return inner

    @staticmethod
    def by_resource_group_ends_with(resource_group: str) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ScalingGroupForProjectRow.scaling_group.like(f"%{resource_group}")

        return inner

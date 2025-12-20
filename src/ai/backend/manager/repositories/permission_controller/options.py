from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import EntityType, RoleSource, ScopeType
from ai.backend.manager.models.rbac_models.permission.object_permission import (
    ObjectPermissionRow,
)
from ai.backend.manager.models.rbac_models.permission.permission_group import (
    PermissionGroupRow,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import QueryCondition, QueryOrder


class RoleConditions:
    """Query conditions for roles."""

    @staticmethod
    def by_name_contains(name: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return RoleRow.name.ilike(f"%{name}%")  # type: ignore[attr-defined]
            else:
                return RoleRow.name.like(f"%{name}%")  # type: ignore[attr-defined]

        return inner

    @staticmethod
    def by_name_equals(name: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(RoleRow.name) == name.lower()
            else:
                return RoleRow.name == name

        return inner

    @staticmethod
    def by_sources(sources: list[RoleSource]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.source.in_(sources)  # type: ignore[attr-defined]

        return inner

    @staticmethod
    def by_statuses(statuses: list[RoleStatus]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RoleRow.status.in_(statuses)  # type: ignore[attr-defined]

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RoleRow.created_at).where(RoleRow.id == cursor_uuid).scalar_subquery()
            )
            return RoleRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to get created_at of the cursor row and compare.
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(RoleRow.created_at).where(RoleRow.id == cursor_uuid).scalar_subquery()
            )
            return RoleRow.created_at > subquery

        return inner

    @staticmethod
    def by_scope_type(scope_type: ScopeType) -> QueryCondition:
        """Filter roles by scope type.

        Requires JOIN with PermissionGroupRow.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionGroupRow.scope_type == scope_type  # type: ignore[attr-defined]

        return inner

    @staticmethod
    def by_scope_id(scope_id: str) -> QueryCondition:
        """Filter roles by scope ID.

        Requires JOIN with PermissionGroupRow.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionGroupRow.scope_id == scope_id  # type: ignore[attr-defined]

        return inner

    @staticmethod
    def by_has_permission_for(entity_type: EntityType) -> QueryCondition:
        """Filter roles having permission for entity type.

        Requires JOIN with ObjectPermissionRow.
        """

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ObjectPermissionRow.entity_type == entity_type  # type: ignore[attr-defined]

        return inner


class RoleOrders:
    """Query orders for roles."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoleRow.name.asc()  # type: ignore[attr-defined]
        else:
            return RoleRow.name.desc()  # type: ignore[attr-defined]

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoleRow.created_at.asc()  # type: ignore[attr-defined]
        else:
            return RoleRow.created_at.desc()  # type: ignore[attr-defined]

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoleRow.updated_at.asc()  # type: ignore[union-attr]
        else:
            return RoleRow.updated_at.desc()  # type: ignore[union-attr]


class AssignedUserConditions:
    """Query conditions for assigned users."""

    @staticmethod
    def by_role_id(role_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.role_id == role_id  # type: ignore[attr-defined]

        return inner

    @staticmethod
    def by_username_contains(username: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return UserRow.username.ilike(f"%{username}%")  # type: ignore[attr-defined]
            else:
                return UserRow.username.like(f"%{username}%")  # type: ignore[attr-defined]

        return inner

    @staticmethod
    def by_username_equals(username: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(UserRow.username) == username.lower()
            else:
                return UserRow.username == username

        return inner

    @staticmethod
    def by_email_contains(email: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return UserRow.email.ilike(f"%{email}%")  # type: ignore[attr-defined]
            else:
                return UserRow.email.like(f"%{email}%")  # type: ignore[attr-defined]

        return inner

    @staticmethod
    def by_email_equals(email: str, case_insensitive: bool = False) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            if case_insensitive:
                return sa.func.lower(UserRow.email) == email.lower()
            else:
                return UserRow.email == email

        return inner

    @staticmethod
    def by_granted_by_equals(granted_by: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return UserRoleRow.granted_by == granted_by  # type: ignore[attr-defined]

        return inner


class AssignedUserOrders:
    """Query orders for assigned users."""

    @staticmethod
    def username(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.username.asc()  # type: ignore[attr-defined]
        else:
            return UserRow.username.desc()  # type: ignore[attr-defined]

    @staticmethod
    def email(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.email.asc()  # type: ignore[attr-defined]
        else:
            return UserRow.email.desc()  # type: ignore[attr-defined]

    @staticmethod
    def granted_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRoleRow.granted_at.asc()  # type: ignore[attr-defined]
        else:
            return UserRoleRow.granted_at.desc()  # type: ignore[attr-defined]

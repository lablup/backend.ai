"""Query conditions for permission rows."""

from __future__ import annotations

import uuid
from collections.abc import Collection
from datetime import datetime

import sqlalchemy as sa

from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.filter_specs import UUIDEqualMatchSpec, UUIDInMatchSpec
from ai.backend.manager.data.permission.types import Permission
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.condition_utils import StringConditions
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow

__all__ = ("ScopedPermissionConditions",)


class ScopedPermissionConditions:
    """Query conditions for scoped permissions."""

    @staticmethod
    def by_entity_type(entity_type: EntityType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.entity_type == entity_type

        return inner

    @staticmethod
    def by_permission(permission: Permission) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.permission == permission

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        """Cursor condition for forward pagination (after cursor).

        Uses subquery to look up created_at of the cursor row (default order: created_at DESC).
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(PermissionRow.created_at)
                .where(PermissionRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return PermissionRow.created_at < subquery

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        """Cursor condition for backward pagination (before cursor).

        Uses subquery to look up created_at of the cursor row (default order: created_at DESC).
        """
        cursor_uuid = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            subquery = (
                sa.select(PermissionRow.created_at)
                .where(PermissionRow.id == cursor_uuid)
                .scalar_subquery()
            )
            return PermissionRow.created_at > subquery

        return inner

    @staticmethod
    def by_created_at_before(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.created_at <= dt

        return inner

    @staticmethod
    def by_created_at_after(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.created_at >= dt

        return inner

    @staticmethod
    def by_created_at_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.created_at == dt

        return inner

    @staticmethod
    def by_created_at_not_equals(dt: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.created_at != dt

        return inner

    @staticmethod
    def by_role_id(role_id: uuid.UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.role_id == role_id

        return inner

    @staticmethod
    def by_ids(permission_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.id.in_(permission_ids)

        return inner

    @staticmethod
    def by_role_ids(role_ids: Collection[uuid.UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.role_id.in_(role_ids)

        return inner

    # ---------------- UUIDFilter / StringFilter factories ----------------

    @staticmethod
    def by_role_id_equals(spec: UUIDEqualMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = PermissionRow.role_id == spec.value
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    @staticmethod
    def by_role_id_in(spec: UUIDInMatchSpec) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            condition = PermissionRow.role_id.in_(spec.values)
            if spec.negated:
                condition = sa.not_(condition)
            return condition

        return inner

    by_entity_type_match = StringConditions(PermissionRow.entity_type)

    @staticmethod
    def by_permission_equals(permission: Permission) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.permission == permission

        return inner

    @staticmethod
    def by_permission_not_equals(permission: Permission) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.permission != permission

        return inner

    @staticmethod
    def by_permission_in(permissions: Collection[Permission]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.permission.in_(list(permissions))

        return inner

    @staticmethod
    def by_permission_not_in(permissions: Collection[Permission]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return PermissionRow.permission.not_in(list(permissions))

        return inner

"""Query conditions for role permission preset rows."""

from __future__ import annotations

from collections.abc import Collection
from datetime import datetime
from uuid import UUID

import sqlalchemy as sa

from ai.backend.common.data.permission.types import EntityType, OperationType
from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)

__all__ = ("RolePermissionPresetConditions",)


class RolePermissionPresetConditions:
    @staticmethod
    def by_role_preset_id_equals(role_preset_id: UUID) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.role_preset_id == role_preset_id

        return inner

    @staticmethod
    def by_role_preset_id_in(role_preset_ids: Collection[UUID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.role_preset_id.in_(role_preset_ids)

        return inner

    @staticmethod
    def by_entity_type_equals(entity_type: EntityType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.entity_type == entity_type

        return inner

    @staticmethod
    def by_entity_type_not_equals(entity_type: EntityType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.entity_type != entity_type

        return inner

    @staticmethod
    def by_entity_type_in(entity_types: Collection[EntityType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.entity_type.in_(entity_types)

        return inner

    @staticmethod
    def by_entity_type_not_in(entity_types: Collection[EntityType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.entity_type.notin_(entity_types)

        return inner

    @staticmethod
    def by_operation_equals(operation: OperationType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.operation == operation

        return inner

    @staticmethod
    def by_operation_not_equals(operation: OperationType) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.operation != operation

        return inner

    @staticmethod
    def by_operation_in(operations: Collection[OperationType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.operation.in_(operations)

        return inner

    @staticmethod
    def by_operation_not_in(operations: Collection[OperationType]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.operation.notin_(operations)

        return inner

    @staticmethod
    def by_created_at_equals(value: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.created_at == value

        return inner

    @staticmethod
    def by_created_at_before(value: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.created_at <= value

        return inner

    @staticmethod
    def by_created_at_after(value: datetime) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.created_at >= value

        return inner

    @staticmethod
    def by_cursor_forward(cursor_id: str) -> QueryCondition:
        cursor_uuid = UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.id < cursor_uuid

        return inner

    @staticmethod
    def by_cursor_backward(cursor_id: str) -> QueryCondition:
        cursor_uuid = UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return RolePermissionPresetRow.id > cursor_uuid

        return inner

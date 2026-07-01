"""Query orders for role permission preset rows."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.rbac_models.role_permission_preset.row import (
    RolePermissionPresetRow,
)

__all__ = ("RolePermissionPresetOrders",)


class RolePermissionPresetOrders:
    @staticmethod
    def entity_type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RolePermissionPresetRow.entity_type.asc()
        return RolePermissionPresetRow.entity_type.desc()

    @staticmethod
    def operation(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RolePermissionPresetRow.operation.asc()
        return RolePermissionPresetRow.operation.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RolePermissionPresetRow.created_at.asc()
        return RolePermissionPresetRow.created_at.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RolePermissionPresetRow.id.asc()
        return RolePermissionPresetRow.id.desc()

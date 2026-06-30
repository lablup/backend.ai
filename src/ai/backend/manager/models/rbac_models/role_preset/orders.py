"""Query orders for role preset rows."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.rbac_models.role_preset.row import RolePresetRow

__all__ = ("RolePresetOrders",)


class RolePresetOrders:
    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RolePresetRow.name.asc()
        return RolePresetRow.name.desc()

    @staticmethod
    def scope_type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RolePresetRow.scope_type.asc()
        return RolePresetRow.scope_type.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RolePresetRow.created_at.asc()
        return RolePresetRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RolePresetRow.updated_at.asc()
        return RolePresetRow.updated_at.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RolePresetRow.id.asc()
        return RolePresetRow.id.desc()

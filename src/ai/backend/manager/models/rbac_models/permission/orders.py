"""Query orders for permission rows."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow

__all__ = ("ScopedPermissionOrders",)


class ScopedPermissionOrders:
    """Query orders for scoped permissions."""

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return PermissionRow.id.asc()
        return PermissionRow.id.desc()

    @staticmethod
    def entity_type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return PermissionRow.entity_type.asc()
        return PermissionRow.entity_type.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return PermissionRow.created_at.asc()
        return PermissionRow.created_at.desc()

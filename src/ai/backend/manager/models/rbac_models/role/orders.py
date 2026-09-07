"""Query orders for role rows."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.rbac_models.role.row import RoleRow

__all__ = ("RoleOrders",)


class RoleOrders:
    """Query orders for roles."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoleRow.name.asc()
        return RoleRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoleRow.created_at.asc()
        return RoleRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoleRow.updated_at.asc()
        return RoleRow.updated_at.desc()

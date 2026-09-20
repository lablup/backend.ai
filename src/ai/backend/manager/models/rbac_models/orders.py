"""Query orders for RBAC models."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user import UserRow


class AssignedUserOrders:
    """Query orders for assigned users."""

    @staticmethod
    def username(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.username.asc()
        return UserRow.username.desc()

    @staticmethod
    def email(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.email.asc()
        return UserRow.email.desc()

    @staticmethod
    def granted_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRoleRow.granted_at.asc()
        return UserRoleRow.granted_at.desc()

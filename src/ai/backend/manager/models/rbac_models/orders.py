"""Query orders for RBAC models."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.project.row import ProjectRow
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


class DomainScopeOrders:
    """Query orders for domain scope IDs."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.name.asc()
        return DomainRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DomainRow.created_at.asc()
        return DomainRow.created_at.desc()


class ProjectScopeOrders:
    """Query orders for project (group) scope IDs."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectRow.name.asc()
        return ProjectRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ProjectRow.created_at.asc()
        return ProjectRow.created_at.desc()


class UserScopeOrders:
    """Query orders for user scope IDs."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        """Order by username."""
        if ascending:
            return UserRow.username.asc()
        return UserRow.username.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return UserRow.created_at.asc()
        return UserRow.created_at.desc()

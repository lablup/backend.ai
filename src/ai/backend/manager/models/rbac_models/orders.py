"""Query orders for RBAC models."""

from __future__ import annotations

from ai.backend.manager.models.domain.row import DomainRow
from ai.backend.manager.models.group.row import GroupRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import (
    ObjectPermissionRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.user import UserRow
from ai.backend.manager.repositories.base import QueryOrder


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
            return GroupRow.name.asc()
        return GroupRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return GroupRow.created_at.asc()
        return GroupRow.created_at.desc()


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


class EntityScopeOrders:
    """Query orders for entity scope search."""

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AssociationScopesEntitiesRow.id.asc()
        return AssociationScopesEntitiesRow.id.desc()

    @staticmethod
    def entity_type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AssociationScopesEntitiesRow.entity_type.asc()
        return AssociationScopesEntitiesRow.entity_type.desc()

    @staticmethod
    def registered_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AssociationScopesEntitiesRow.registered_at.asc()
        return AssociationScopesEntitiesRow.registered_at.desc()


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


class ObjectPermissionOrders:
    """Query orders for object permissions."""

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ObjectPermissionRow.id.asc()
        return ObjectPermissionRow.id.desc()

    @staticmethod
    def entity_type(ascending: bool = True) -> QueryOrder:
        if ascending:
            return ObjectPermissionRow.entity_type.asc()
        return ObjectPermissionRow.entity_type.desc()

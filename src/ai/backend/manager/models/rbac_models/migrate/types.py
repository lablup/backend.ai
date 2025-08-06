from dataclasses import dataclass, field
from typing import Any

from ai.backend.manager.data.permission.association_scopes_entities import (
    AssociationScopesEntitiesCreateInput,
)
from ai.backend.manager.data.permission.role import RoleCreateInput
from ai.backend.manager.data.permission.scope_permission import ScopePermissionCreateInput
from ai.backend.manager.data.permission.user_role import UserRoleCreateInput


@dataclass
class PermissionCreateInputGroup:
    roles: list[RoleCreateInput] = field(default_factory=list)
    user_roles: list[UserRoleCreateInput] = field(default_factory=list)
    scope_permissions: list[ScopePermissionCreateInput] = field(default_factory=list)
    association_scopes_entities: list[AssociationScopesEntitiesCreateInput] = field(
        default_factory=list
    )

    def merge(self, other: "PermissionCreateInputGroup") -> None:
        self.roles.extend(other.roles)
        self.user_roles.extend(other.user_roles)
        self.scope_permissions.extend(other.scope_permissions)
        self.association_scopes_entities.extend(other.association_scopes_entities)

    def to_role_insert_data(self) -> list[dict[str, Any]]:
        return [
            {
                "name": role.name,
                "status": role.status,
                "description": role.description,
            }
            for role in self.roles
        ]

    def to_user_role_insert_data(self) -> list[dict[str, Any]]:
        return [
            {
                "user_id": user_role.user_id,
                "role_id": user_role.role_id,
            }
            for user_role in self.user_roles
        ]

    def to_scope_permission_insert_data(self) -> list[dict[str, Any]]:
        return [
            {
                "role_id": scope_permission.role_id,
                "scope_type": scope_permission.scope_type,
                "scope_id": scope_permission.scope_id,
                "entity_type": scope_permission.entity_type,
                "operation": scope_permission.operation,
            }
            for scope_permission in self.scope_permissions
        ]

    def to_association_scopes_entities_insert_data(self) -> list[dict[str, Any]]:
        return [
            {
                "scope_type": association.scope_id.scope_type,
                "scope_id": association.scope_id.scope_id,
                "entity_id": association.object_id.entity_id,
                "entity_type": association.object_id.entity_type,
            }
            for association in self.association_scopes_entities
        ]

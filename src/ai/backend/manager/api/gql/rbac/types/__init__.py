"""RBAC GraphQL types package."""

from .enums import (
    EntityTypeGQL,
    ObjectPermissionOrderField,
    OperationTypeGQL,
    RoleOrderField,
    RoleSourceGQL,
    ScopedPermissionOrderField,
    ScopeTypeGQL,
)
from .inputs import (
    CreateRoleAssignmentInput,
    CreateRoleInput,
    ObjectPermissionInput,
    ScopedPermissionInput,
    ScopeInput,
    UpdateRoleInput,
    UpdateRolePermissionsInput,
)
from .permission import (
    ObjectPermission,
    ObjectPermissionConnection,
    ObjectPermissionEdge,
    Scope,
    ScopedPermission,
    ScopedPermissionConnection,
    ScopedPermissionEdge,
)
from .role import (
    Role,
    RoleConnection,
    RoleEdge,
    RoleFilter,
    RoleOrderBy,
    RoleSourceFilter,
    ScopeTypeFilter,
)

__all__ = [
    # Enums
    "EntityTypeGQL",
    "ObjectPermissionOrderField",
    "OperationTypeGQL",
    "RoleOrderField",
    "RoleSourceGQL",
    "ScopedPermissionOrderField",
    "ScopeTypeGQL",
    # Inputs
    "CreateRoleAssignmentInput",
    "CreateRoleInput",
    "ObjectPermissionInput",
    "ScopeInput",
    "ScopedPermissionInput",
    "UpdateRoleInput",
    "UpdateRolePermissionsInput",
    # Permissions
    "ObjectPermission",
    "ObjectPermissionConnection",
    "ObjectPermissionEdge",
    "Scope",
    "ScopedPermission",
    "ScopedPermissionConnection",
    "ScopedPermissionEdge",
    # Role
    "Role",
    "RoleConnection",
    "RoleEdge",
    "RoleFilter",
    "RoleOrderBy",
    "RoleSourceFilter",
    "ScopeTypeFilter",
]

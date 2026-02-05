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
from .filters import (
    RoleFilter,
    RoleOrderBy,
    RoleSourceFilter,
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
from .node import (
    ObjectPermission,
    ObjectPermissionConnection,
    ObjectPermissionEdge,
    PermissionGroup,
    PermissionGroupConnection,
    PermissionGroupEdge,
    Role,
    RoleConnection,
    RoleEdge,
    Scope,
    ScopedPermission,
    ScopedPermissionConnection,
    ScopedPermissionEdge,
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
    # Filters
    "RoleFilter",
    "RoleOrderBy",
    "RoleSourceFilter",
    # Inputs
    "CreateRoleAssignmentInput",
    "CreateRoleInput",
    "ObjectPermissionInput",
    "ScopeInput",
    "ScopedPermissionInput",
    "UpdateRoleInput",
    "UpdateRolePermissionsInput",
    # Node types
    "ObjectPermission",
    "ObjectPermissionConnection",
    "ObjectPermissionEdge",
    "PermissionGroup",
    "PermissionGroupConnection",
    "PermissionGroupEdge",
    "Role",
    "RoleConnection",
    "RoleEdge",
    "Scope",
    "ScopedPermission",
    "ScopedPermissionConnection",
    "ScopedPermissionEdge",
]

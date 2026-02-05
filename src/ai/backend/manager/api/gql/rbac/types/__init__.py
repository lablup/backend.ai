"""RBAC GraphQL types package."""

from .enums import (
    EntityTypeGQL,
    ObjectPermissionOrderField,
    OperationTypeGQL,
    PermissionGroupOrderField,
    RoleOrderField,
    RoleSourceGQL,
    ScopedPermissionOrderField,
    ScopeTypeGQL,
)
from .filters import (
    PermissionGroupFilter,
    PermissionGroupOrderBy,
    RoleFilter,
    RoleOrderBy,
    RoleSourceFilter,
    ScopeTypeFilter,
)
from .inputs import (
    CreateRoleAssignmentInput,
    CreateRoleInput,
    DeleteRoleAssignmentInput,
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
    "PermissionGroupOrderField",
    "RoleOrderField",
    "RoleSourceGQL",
    "ScopedPermissionOrderField",
    "ScopeTypeGQL",
    # Filters
    "PermissionGroupFilter",
    "PermissionGroupOrderBy",
    "RoleFilter",
    "RoleOrderBy",
    "RoleSourceFilter",
    "ScopeTypeFilter",
    # Inputs
    "CreateRoleAssignmentInput",
    "CreateRoleInput",
    "DeleteRoleAssignmentInput",
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

"""RBAC GQL types package."""

from .permission import (
    CreatePermissionInput,
    EntityTypeGQL,
    OperationTypeGQL,
    PermissionConnection,
    PermissionEdge,
    PermissionFilter,
    PermissionGQL,
    PermissionOrderBy,
    PermissionOrderField,
    ScopeTypeGQL,
)
from .role import (
    AssignRoleInput,
    CreateRoleInput,
    RevokeRoleInput,
    RoleAssignmentConnection,
    RoleAssignmentEdge,
    RoleAssignmentFilter,
    RoleAssignmentGQL,
    RoleConnection,
    RoleEdge,
    RoleFilter,
    RoleGQL,
    RoleOrderBy,
    RoleOrderField,
    RoleSourceGQL,
    RoleStatusGQL,
    UpdateRoleInput,
)

__all__ = [
    # Permission enums
    "EntityTypeGQL",
    "OperationTypeGQL",
    "ScopeTypeGQL",
    "PermissionOrderField",
    # Role enums
    "RoleSourceGQL",
    "RoleStatusGQL",
    "RoleOrderField",
    # Types
    "PermissionGQL",
    "RoleGQL",
    "RoleAssignmentGQL",
    # Filters
    "PermissionFilter",
    "RoleFilter",
    "RoleAssignmentFilter",
    # OrderBy
    "PermissionOrderBy",
    "RoleOrderBy",
    # Inputs
    "CreatePermissionInput",
    "CreateRoleInput",
    "UpdateRoleInput",
    "AssignRoleInput",
    "RevokeRoleInput",
    # Connections
    "PermissionConnection",
    "PermissionEdge",
    "RoleConnection",
    "RoleEdge",
    "RoleAssignmentConnection",
    "RoleAssignmentEdge",
]

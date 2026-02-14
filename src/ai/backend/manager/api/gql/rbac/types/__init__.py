"""RBAC GQL types package."""

from .entity import (
    EntityConnection,
    EntityEdge,
    EntityNode,
)
from .permission import (
    CreatePermissionInput,
    DeletePermissionInput,
    DeletePermissionPayload,
    EntityTypeGQL,
    OperationTypeGQL,
    PermissionConnection,
    PermissionEdge,
    PermissionFilter,
    PermissionGQL,
    PermissionOrderBy,
    PermissionOrderField,
)
from .role import (
    AssignRoleInput,
    CreateRoleInput,
    DeleteRoleInput,
    DeleteRolePayload,
    PurgeRoleInput,
    PurgeRolePayload,
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
    "DeletePermissionInput",
    "CreateRoleInput",
    "UpdateRoleInput",
    "DeleteRoleInput",
    "PurgeRoleInput",
    "AssignRoleInput",
    "RevokeRoleInput",
    # Payloads
    "DeletePermissionPayload",
    "DeleteRolePayload",
    "PurgeRolePayload",
    # Connections
    "PermissionConnection",
    "PermissionEdge",
    "RoleConnection",
    "RoleEdge",
    "RoleAssignmentConnection",
    "RoleAssignmentEdge",
    # Entity types
    "EntityNode",
    "EntityEdge",
    "EntityConnection",
]

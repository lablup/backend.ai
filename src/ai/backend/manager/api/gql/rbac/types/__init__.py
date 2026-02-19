"""RBAC GQL types package."""

from .entity import (
    EntityConnection,
    EntityEdge,
    EntityFilter,
    EntityOrderBy,
    EntityOrderField,
    EntityRefGQL,
)
from .entity_node import EntityNode
from .permission import (
    CreatePermissionInput,
    DeletePermissionInput,
    DeletePermissionPayload,
    OperationTypeGQL,
    PermissionConnection,
    PermissionEdge,
    PermissionFilter,
    PermissionGQL,
    PermissionOrderBy,
    PermissionOrderField,
    RBACElementTypeGQL,
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
    "RBACElementTypeGQL",
    "OperationTypeGQL",
    "PermissionOrderField",
    # Role enums
    "RoleSourceGQL",
    "RoleStatusGQL",
    "RoleOrderField",
    # Entity enums
    "EntityOrderField",
    # Types
    "PermissionGQL",
    "RoleGQL",
    "RoleAssignmentGQL",
    "EntityRefGQL",
    # Filters
    "PermissionFilter",
    "RoleFilter",
    "RoleAssignmentFilter",
    "EntityFilter",
    # OrderBy
    "PermissionOrderBy",
    "RoleOrderBy",
    "EntityOrderBy",
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

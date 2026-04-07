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
    EntityActionInfoGQL,
    EntityOperationCombinationGQL,
    OperationInfoGQL,
    OperationTypeGQL,
    PermissionConnection,
    PermissionEdge,
    PermissionFilter,
    PermissionGQL,
    PermissionNestedFilterGQL,
    PermissionOrderBy,
    PermissionOrderField,
    ScopeEntityCombinationGQL,
    ScopeEntityOperationCombinationGQL,
    UpdatePermissionInput,
)
from .role import (
    AssignRoleInput,
    BulkAssignRoleErrorGQL,
    BulkAssignRoleInputGQL,
    BulkAssignRolePayloadGQL,
    BulkRevokeRoleErrorGQL,
    BulkRevokeRoleInputGQL,
    BulkRevokeRolePayloadGQL,
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
    RoleAssignmentOrderBy,
    RoleAssignmentOrderField,
    RoleAssignmentRoleNestedFilterGQL,
    RoleConnection,
    RoleEdge,
    RoleFilter,
    RoleGQL,
    RoleOrderBy,
    RoleOrderField,
    RoleSourceFilterGQL,
    RoleSourceGQL,
    RoleStatusFilterGQL,
    RoleStatusGQL,
    UpdateRoleInput,
)
from .scope import RBACElementTypeGQL, ScopeInputGQL

__all__ = [
    # Permission enums
    "RBACElementTypeGQL",
    "OperationTypeGQL",
    "PermissionOrderField",
    # Role enums
    "RoleSourceGQL",
    "RoleStatusGQL",
    # Role filter wrappers
    "RoleSourceFilterGQL",
    "RoleStatusFilterGQL",
    "RoleOrderField",
    "RoleAssignmentOrderField",
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
    "RoleAssignmentRoleNestedFilterGQL",
    "PermissionNestedFilterGQL",
    "EntityFilter",
    # OrderBy
    "PermissionOrderBy",
    "RoleOrderBy",
    "RoleAssignmentOrderBy",
    "EntityOrderBy",
    # Inputs
    "CreatePermissionInput",
    "UpdatePermissionInput",
    "DeletePermissionInput",
    "CreateRoleInput",
    "UpdateRoleInput",
    "DeleteRoleInput",
    "PurgeRoleInput",
    "AssignRoleInput",
    "RevokeRoleInput",
    "BulkAssignRoleInputGQL",
    "BulkRevokeRoleInputGQL",
    # Payloads
    "DeletePermissionPayload",
    "DeleteRolePayload",
    "PurgeRolePayload",
    "BulkAssignRoleErrorGQL",
    "BulkAssignRolePayloadGQL",
    "BulkRevokeRoleErrorGQL",
    "BulkRevokeRolePayloadGQL",
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
    # Scope input
    "ScopeInputGQL",
    # Scope-entity combination
    "ScopeEntityCombinationGQL",
    # Entity-operation combination
    "EntityOperationCombinationGQL",
    "OperationInfoGQL",
    # Scope-entity-operation combination (permission matrix)
    "EntityActionInfoGQL",
    "ScopeEntityOperationCombinationGQL",
]

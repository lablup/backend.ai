"""RBAC GraphQL types package."""

from .enums import (
    EntityTypeGQL,
    ObjectPermissionOrderField,
    OperationTypeGQL,
    RoleOrderField,
    RoleSourceGQL,
    RoleStatusGQL,
    ScopedPermissionOrderField,
    ScopeTypeGQL,
)
from .inputs import (
    CreateRoleAssignmentInput,
    CreateRoleInput,
    DeleteRoleAssignmentInput,
    DeleteRoleInput,
    PurgeRoleInput,
    ScopeInput,
    UpdateRoleInput,
    UpdateRolePermissionsInput,
)
from .permission import (
    ObjectPermission,
    ObjectPermissionConnection,
    ObjectPermissionEdge,
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
from .role_info import (
    RoleIdentityInfo,
    RoleLifecycleInfo,
)
from .scope import (
    Scope,
    ScopeConnection,
    ScopeEdge,
)

__all__ = [
    # Enums
    "EntityTypeGQL",
    "ObjectPermissionOrderField",
    "OperationTypeGQL",
    "RoleOrderField",
    "RoleSourceGQL",
    "RoleStatusGQL",
    "ScopedPermissionOrderField",
    "ScopeTypeGQL",
    # Inputs
    "CreateRoleAssignmentInput",
    "CreateRoleInput",
    "DeleteRoleAssignmentInput",
    "DeleteRoleInput",
    "PurgeRoleInput",
    "ScopeInput",
    "UpdateRoleInput",
    "UpdateRolePermissionsInput",
    # Permissions
    "ObjectPermission",
    "ObjectPermissionConnection",
    "ObjectPermissionEdge",
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
    # Role Info
    "RoleIdentityInfo",
    "RoleLifecycleInfo",
    # Scope
    "Scope",
    "ScopeConnection",
    "ScopeEdge",
]

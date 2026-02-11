from __future__ import annotations

from .resolver import (
    admin_assign_role,
    admin_create_permission,
    admin_create_role,
    admin_delete_permission,
    admin_delete_role,
    admin_permissions,
    admin_purge_role,
    admin_revoke_role,
    admin_role,
    admin_role_assignments,
    admin_roles,
    admin_update_role,
    entity_types,
    scope_types,
)
from .types import (
    AssignRoleInput,
    CreatePermissionInput,
    CreateRoleInput,
    EntityTypeGQL,
    OperationTypeGQL,
    PermissionConnection,
    PermissionFilter,
    PermissionGQL,
    PermissionOrderBy,
    RevokeRoleInput,
    RoleAssignmentConnection,
    RoleAssignmentFilter,
    RoleAssignmentGQL,
    RoleConnection,
    RoleFilter,
    RoleGQL,
    RoleOrderBy,
    RoleSourceGQL,
    RoleStatusGQL,
    ScopeTypeGQL,
    UpdateRoleInput,
)

__all__ = (
    # Enums
    "EntityTypeGQL",
    "OperationTypeGQL",
    "ScopeTypeGQL",
    "RoleSourceGQL",
    "RoleStatusGQL",
    # Types
    "RoleGQL",
    "PermissionGQL",
    "RoleAssignmentGQL",
    # Filters
    "RoleFilter",
    "PermissionFilter",
    "RoleAssignmentFilter",
    # OrderBy
    "RoleOrderBy",
    "PermissionOrderBy",
    # Inputs
    "CreateRoleInput",
    "UpdateRoleInput",
    "CreatePermissionInput",
    "AssignRoleInput",
    "RevokeRoleInput",
    # Connections
    "RoleConnection",
    "PermissionConnection",
    "RoleAssignmentConnection",
    # Query resolvers
    "admin_role",
    "admin_roles",
    "admin_permissions",
    "admin_role_assignments",
    "scope_types",
    "entity_types",
    # Mutation resolvers
    "admin_create_role",
    "admin_update_role",
    "admin_delete_role",
    "admin_purge_role",
    "admin_create_permission",
    "admin_delete_permission",
    "admin_assign_role",
    "admin_revoke_role",
)

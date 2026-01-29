"""RBAC resolver package.

Contains GraphQL query and mutation resolver functions for the RBAC module.
"""

from .role import (
    create_role,
    create_role_assignment,
    delete_role,
    delete_role_assignment,
    purge_role,
    role,
    role_object_permissions,
    role_scopes,
    roles,
    scope_permissions,
    update_role,
    update_role_permissions,
)

__all__ = [
    # Query resolvers
    "role",
    "roles",
    "role_scopes",
    "role_object_permissions",
    "scope_permissions",
    # Mutation resolvers
    "create_role",
    "update_role",
    "delete_role",
    "purge_role",
    "update_role_permissions",
    "create_role_assignment",
    "delete_role_assignment",
]

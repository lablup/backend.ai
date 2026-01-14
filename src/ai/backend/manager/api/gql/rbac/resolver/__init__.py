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
    roles,
    update_role,
    update_role_permissions,
)

__all__ = [
    # Query resolvers
    "role",
    "roles",
    # Mutation resolvers
    "create_role",
    "update_role",
    "delete_role",
    "purge_role",
    "update_role_permissions",
    "create_role_assignment",
    "delete_role_assignment",
]

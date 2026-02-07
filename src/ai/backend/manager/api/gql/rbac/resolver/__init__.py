"""RBAC resolver package.

Contains GraphQL query and mutation resolver functions for the RBAC module.
"""

from .permission_group import (
    admin_permission_groups,
)
from .role import (
    admin_create_role,
    admin_create_role_assignment,
    admin_delete_role,
    admin_delete_role_assignment,
    admin_purge_role,
    admin_role,
    admin_roles,
    admin_update_role,
    admin_update_role_permissions,
)

__all__ = [
    # Query resolvers
    "admin_role",
    "admin_roles",
    "admin_permission_groups",
    # Mutation resolvers
    "admin_create_role",
    "admin_update_role",
    "admin_delete_role",
    "admin_purge_role",
    "admin_update_role_permissions",
    "admin_create_role_assignment",
    "admin_delete_role_assignment",
]

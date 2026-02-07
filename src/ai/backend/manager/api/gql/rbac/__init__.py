"""GraphQL API for RBAC (Role-Based Access Control) system.

This module provides GraphQL types, resolvers, and fetchers for the RBAC domain.
It follows the fetcher/resolver/types pattern for organizing GraphQL code.

Structure:
- types/: GraphQL type definitions (Node, Connection, Filter, OrderBy, Input)
- fetcher/: Data loading functions (pagination specs)
- resolver/: GraphQL operations (Query, Mutation resolvers)
"""

from .resolver import (
    admin_create_role,
    admin_create_role_assignment,
    admin_delete_role,
    admin_delete_role_assignment,
    admin_permission_groups,
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

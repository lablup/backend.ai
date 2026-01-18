"""GraphQL API for RBAC (Role-Based Access Control) system.

This module provides GraphQL types, resolvers, and fetchers for the RBAC domain.
It follows the fetcher/resolver/types pattern for organizing GraphQL code.

Structure:
- types/: GraphQL type definitions (Node, Connection, Filter, OrderBy, Input)
- fetcher/: Data loading functions (pagination specs)
- resolver/: GraphQL operations (Query, Mutation resolvers)
"""

from .resolver import (
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

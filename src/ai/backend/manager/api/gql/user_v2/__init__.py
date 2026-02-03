"""User V2 GraphQL API package.

Added in 26.2.0. Provides structured user management API with typed fields
replacing JSON scalars and organized into logical field groups.
"""

from .resolver import (
    # Mutations
    admin_bulk_create_users,
    admin_create_user,
    admin_delete_user,
    admin_delete_users,
    admin_purge_user,
    admin_purge_users,
    admin_update_user,
    # Queries
    admin_user_v2,
    admin_users,
    domain_users,
    project_users,
    update_user,
    user_v2,
)

__all__ = [
    # Queries
    "admin_user_v2",
    "admin_users",
    "domain_users",
    "project_users",
    "user_v2",
    # Mutations
    "admin_create_user",
    "admin_bulk_create_users",
    "admin_update_user",
    "update_user",
    "admin_delete_user",
    "admin_delete_users",
    "admin_purge_user",
    "admin_purge_users",
]

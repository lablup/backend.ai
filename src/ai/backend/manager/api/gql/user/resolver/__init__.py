"""User GraphQL resolver package."""

from .mutation import (
    admin_bulk_create_users,
    admin_bulk_purge_users_v2,
    admin_bulk_update_users_v2,
    admin_create_user,
    admin_delete_user,
    admin_delete_users,
    admin_purge_user,
    admin_update_user,
    update_user,
)
from .query import (
    admin_user_v2,
    admin_users_v2,
    domain_users_v2,
    my_user_v2,
    project_users_v2,
)

__all__ = [
    # Queries
    "admin_user_v2",
    "admin_users_v2",
    "domain_users_v2",
    "my_user_v2",
    "project_users_v2",
    # Mutations
    "admin_create_user",
    "admin_bulk_create_users",
    "admin_bulk_update_users_v2",
    "admin_update_user",
    "update_user",
    "admin_delete_user",
    "admin_delete_users",
    "admin_purge_user",
    "admin_bulk_purge_users_v2",
]

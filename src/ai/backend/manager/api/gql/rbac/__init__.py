"""GraphQL API for RBAC (Role-Based Access Control) system."""

from .resolver import (
    create_role,
    create_role_assignment,
    delete_role,
    delete_role_assignment,
    role,
    roles,
    update_role,
    update_role_permissions,
)

__all__ = [
    "role",
    "roles",
    "create_role",
    "update_role",
    "delete_role",
    "update_role_permissions",
    "create_role_assignment",
    "delete_role_assignment",
]

"""RBAC GQL resolvers package."""

from .entity import admin_entities
from .permission import (
    admin_create_permission,
    admin_delete_permission,
    admin_permissions,
    entity_types,
    scope_types,
)
from .role import (
    admin_assign_role,
    admin_create_role,
    admin_delete_role,
    admin_purge_role,
    admin_revoke_role,
    admin_role,
    admin_role_assignments,
    admin_roles,
    admin_update_role,
)

__all__ = [
    # Permission queries
    "admin_permissions",
    "scope_types",
    "entity_types",
    # Entity queries
    "admin_entities",
    # Permission mutations
    "admin_create_permission",
    "admin_delete_permission",
    # Role queries
    "admin_role",
    "admin_roles",
    "admin_role_assignments",
    # Role mutations
    "admin_create_role",
    "admin_update_role",
    "admin_delete_role",
    "admin_purge_role",
    "admin_assign_role",
    "admin_revoke_role",
]

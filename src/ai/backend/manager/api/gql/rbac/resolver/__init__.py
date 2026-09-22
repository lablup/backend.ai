"""RBAC GQL resolvers package."""

from .permission import (
    admin_bulk_add_role_permissions,
    admin_bulk_remove_role_permissions,
    admin_create_permission,
    admin_delete_permission,
    admin_permissions,
    admin_replace_role_permissions,
    admin_update_permission,
    my_atomic_bulk_scope_permissions,
    my_scope_permissions,
    rbac_entity_operation_combinations,
    rbac_permission_matrix,
    rbac_scope_entity_combinations,
)
from .role import (
    admin_assign_role,
    admin_bulk_assign_role,
    admin_bulk_revoke_role,
    admin_create_role,
    admin_delete_role,
    admin_purge_role,
    admin_revoke_role,
    admin_role,
    admin_role_assignments,
    admin_roles,
    admin_update_role,
    my_roles,
    my_roles_v2,
    project_roles,
)

__all__ = [
    # Permission queries
    "admin_permissions",
    "rbac_entity_operation_combinations",
    "rbac_permission_matrix",
    "rbac_scope_entity_combinations",
    # Entity queries
    # Permission mutations
    "admin_create_permission",
    "admin_update_permission",
    "admin_delete_permission",
    "admin_bulk_add_role_permissions",
    "admin_bulk_remove_role_permissions",
    "admin_replace_role_permissions",
    # Role queries
    "admin_role",
    "admin_roles",
    "admin_role_assignments",
    "my_roles",
    "my_roles_v2",
    "my_atomic_bulk_scope_permissions",
    "my_scope_permissions",
    "project_roles",
    # Role mutations
    "admin_create_role",
    "admin_update_role",
    "admin_delete_role",
    "admin_purge_role",
    "admin_assign_role",
    "admin_revoke_role",
    "admin_bulk_assign_role",
    "admin_bulk_revoke_role",
]

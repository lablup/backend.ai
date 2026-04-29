"""RBAC GQL resolvers package."""

from .entity import admin_entities
from .permission import (
    admin_bulk_add_role_permissions,
    admin_bulk_remove_role_permissions,
    admin_create_permission,
    admin_delete_permission,
    admin_permissions,
    admin_replace_role_permissions,
    admin_update_permission,
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
    project_roles,
)
from .role_invitation import (
    accept_role_invitation,
    admin_cancel_role_invitation,
    admin_role_invitations,
    create_role_invitation,
    my_role_invitations,
    my_sent_role_invitations,
    reject_role_invitation,
    role_scoped_role_invitations,
)

__all__ = [
    # Permission queries
    "admin_permissions",
    "rbac_entity_operation_combinations",
    "rbac_permission_matrix",
    "rbac_scope_entity_combinations",
    # Entity queries
    "admin_entities",
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
    # Role invitation queries
    "my_role_invitations",
    "my_sent_role_invitations",
    "role_scoped_role_invitations",
    "admin_role_invitations",
    # Role invitation mutations
    "create_role_invitation",
    "accept_role_invitation",
    "reject_role_invitation",
    "admin_cancel_role_invitation",
]

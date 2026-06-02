"""Role preset GQL resolvers."""

from .mutation import (
    admin_bulk_add_role_preset_permissions,
    admin_bulk_remove_role_preset_permissions,
    admin_create_role_preset,
    admin_delete_role_presets,
    admin_purge_role_presets,
    admin_restore_role_presets,
    admin_update_role_preset,
)
from .query import (
    admin_role_preset,
    admin_role_presets,
)

__all__ = [
    # Queries
    "admin_role_preset",
    "admin_role_presets",
    # Mutations
    "admin_create_role_preset",
    "admin_update_role_preset",
    "admin_delete_role_presets",
    "admin_restore_role_presets",
    "admin_purge_role_presets",
    "admin_bulk_add_role_preset_permissions",
    "admin_bulk_remove_role_preset_permissions",
]

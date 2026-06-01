"""Role preset GraphQL API package."""

from .resolver import (
    admin_bulk_add_role_preset_permissions,
    admin_bulk_remove_role_preset_permissions,
    admin_create_role_preset,
    admin_purge_role_presets,
    admin_role_preset,
    admin_role_presets,
)
from .types import (
    BulkAddRolePermissionPresetFailureInfoGQL,
    BulkAddRolePermissionPresetsInputGQL,
    BulkAddRolePermissionPresetsPayloadGQL,
    BulkPurgeRolePresetsInputGQL,
    BulkPurgeRolePresetsPayloadGQL,
    BulkRemoveRolePermissionPresetsInputGQL,
    BulkRemoveRolePermissionPresetsPayloadGQL,
    BulkRolePermissionPresetFailureInfoGQL,
    BulkRolePresetFailureInfoGQL,
    CreateRolePresetInputGQL,
    CreateRolePresetPayloadGQL,
    RolePermissionPresetConnection,
    RolePermissionPresetEdge,
    RolePermissionPresetEntryInputGQL,
    RolePermissionPresetFilterGQL,
    RolePermissionPresetGQL,
    RolePermissionPresetOrderByGQL,
    RolePermissionPresetOrderFieldGQL,
    RolePresetConnection,
    RolePresetEdge,
    RolePresetFilterGQL,
    RolePresetGQL,
    RolePresetOrderByGQL,
    RolePresetOrderFieldGQL,
)

__all__ = [
    # Queries
    "admin_role_preset",
    "admin_role_presets",
    # Mutations
    "admin_create_role_preset",
    "admin_purge_role_presets",
    "admin_bulk_add_role_preset_permissions",
    "admin_bulk_remove_role_preset_permissions",
    # Node / Connection types
    "RolePresetGQL",
    "RolePresetEdge",
    "RolePresetConnection",
    "RolePermissionPresetGQL",
    "RolePermissionPresetEdge",
    "RolePermissionPresetConnection",
    # Filter / OrderBy types
    "RolePresetFilterGQL",
    "RolePresetOrderByGQL",
    "RolePresetOrderFieldGQL",
    "RolePermissionPresetFilterGQL",
    "RolePermissionPresetOrderByGQL",
    "RolePermissionPresetOrderFieldGQL",
    # Input types
    "CreateRolePresetInputGQL",
    "BulkPurgeRolePresetsInputGQL",
    "RolePermissionPresetEntryInputGQL",
    "BulkAddRolePermissionPresetsInputGQL",
    "BulkRemoveRolePermissionPresetsInputGQL",
    # Payload types
    "CreateRolePresetPayloadGQL",
    "BulkRolePresetFailureInfoGQL",
    "BulkPurgeRolePresetsPayloadGQL",
    "BulkRolePermissionPresetFailureInfoGQL",
    "BulkAddRolePermissionPresetFailureInfoGQL",
    "BulkAddRolePermissionPresetsPayloadGQL",
    "BulkRemoveRolePermissionPresetsPayloadGQL",
]

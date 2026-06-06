"""Role preset GQL types."""

from .filters import (
    RolePresetFilterGQL,
    RolePresetOrderByGQL,
    RolePresetOrderFieldGQL,
)
from .inputs import (
    BulkAddRolePermissionPresetsInputGQL,
    BulkDeleteRolePresetsInputGQL,
    BulkPurgeRolePresetsInputGQL,
    BulkRemoveRolePermissionPresetsInputGQL,
    BulkRestoreRolePresetsInputGQL,
    CreateRolePresetInputGQL,
    RolePermissionPresetEntryInputGQL,
    UpdateRolePresetInputGQL,
)
from .node import (
    RolePresetConnection,
    RolePresetEdge,
    RolePresetGQL,
)
from .payloads import (
    BulkDeleteRolePresetsPayloadGQL,
    BulkPurgeRolePresetsPayloadGQL,
    BulkRestoreRolePresetsPayloadGQL,
    BulkRolePresetFailureInfoGQL,
    CreateRolePresetPayloadGQL,
    UpdateRolePresetPayloadGQL,
)
from .permission import (
    BulkAddRolePermissionPresetFailureInfoGQL,
    BulkAddRolePermissionPresetsPayloadGQL,
    BulkRemoveRolePermissionPresetsPayloadGQL,
    BulkRolePermissionPresetFailureInfoGQL,
    RolePermissionPresetConnection,
    RolePermissionPresetEdge,
    RolePermissionPresetFilterGQL,
    RolePermissionPresetGQL,
    RolePermissionPresetOrderByGQL,
    RolePermissionPresetOrderFieldGQL,
)

__all__ = [
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
    "UpdateRolePresetInputGQL",
    "BulkDeleteRolePresetsInputGQL",
    "BulkRestoreRolePresetsInputGQL",
    "BulkPurgeRolePresetsInputGQL",
    "RolePermissionPresetEntryInputGQL",
    "BulkAddRolePermissionPresetsInputGQL",
    "BulkRemoveRolePermissionPresetsInputGQL",
    # Payload types
    "CreateRolePresetPayloadGQL",
    "UpdateRolePresetPayloadGQL",
    "BulkRolePresetFailureInfoGQL",
    "BulkDeleteRolePresetsPayloadGQL",
    "BulkRestoreRolePresetsPayloadGQL",
    "BulkPurgeRolePresetsPayloadGQL",
    "BulkRolePermissionPresetFailureInfoGQL",
    "BulkAddRolePermissionPresetFailureInfoGQL",
    "BulkAddRolePermissionPresetsPayloadGQL",
    "BulkRemoveRolePermissionPresetsPayloadGQL",
]

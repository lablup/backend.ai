"""Role preset GQL types."""

from .filters import (
    RolePresetFilterGQL,
    RolePresetOrderByGQL,
    RolePresetOrderFieldGQL,
)
from .inputs import (
    BulkAddRolePermissionPresetsInputGQL,
    BulkPurgeRolePresetsInputGQL,
    BulkRemoveRolePermissionPresetsInputGQL,
    CreateRolePresetInputGQL,
    RolePermissionPresetEntryInputGQL,
)
from .node import (
    RolePresetConnection,
    RolePresetEdge,
    RolePresetGQL,
)
from .payloads import (
    BulkPurgeRolePresetsPayloadGQL,
    BulkRolePresetFailureInfoGQL,
    CreateRolePresetPayloadGQL,
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

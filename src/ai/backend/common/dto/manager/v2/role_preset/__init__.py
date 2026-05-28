"""
Role Preset DTO v2 models for Manager API.
"""

from ai.backend.common.dto.manager.v2.role_preset.request import (
    BulkAddRolePresetPermissionsInput,
    BulkRemoveRolePresetPermissionsInput,
    CreateRolePresetInput,
    DeleteRolePresetInput,
    PurgeRolePresetInput,
    RestoreRolePresetInput,
    RolePresetFilter,
    RolePresetOrder,
    SearchRolePresetsInput,
    UpdateRolePresetInput,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    BulkAddRolePresetPermissionsPayload,
    BulkRemoveRolePresetPermissionFailureInfo,
    BulkRemoveRolePresetPermissionsPayload,
    CreateRolePresetPayload,
    DeleteRolePresetPayload,
    PurgeRolePresetPayload,
    RestoreRolePresetPayload,
    RolePermissionPresetNode,
    RolePresetNode,
    SearchRolePresetsPayload,
    UpdateRolePresetPayload,
)
from ai.backend.common.dto.manager.v2.role_preset.types import (
    EntityType,
    OperationTypeDTO,
    OrderDirection,
    RBACElementTypeDTO,
    RolePermissionPresetEntry,
    RolePresetOrderField,
)

__all__ = (
    # Types
    "EntityType",
    "OperationTypeDTO",
    "OrderDirection",
    "RBACElementTypeDTO",
    "RolePermissionPresetEntry",
    "RolePresetOrderField",
    # Request DTOs
    "BulkAddRolePresetPermissionsInput",
    "BulkRemoveRolePresetPermissionsInput",
    "CreateRolePresetInput",
    "DeleteRolePresetInput",
    "PurgeRolePresetInput",
    "RestoreRolePresetInput",
    "RolePresetFilter",
    "RolePresetOrder",
    "SearchRolePresetsInput",
    "UpdateRolePresetInput",
    # Response DTOs
    "BulkAddRolePresetPermissionsPayload",
    "BulkRemoveRolePresetPermissionFailureInfo",
    "BulkRemoveRolePresetPermissionsPayload",
    "CreateRolePresetPayload",
    "DeleteRolePresetPayload",
    "PurgeRolePresetPayload",
    "RestoreRolePresetPayload",
    "RolePermissionPresetNode",
    "RolePresetNode",
    "SearchRolePresetsPayload",
    "UpdateRolePresetPayload",
)

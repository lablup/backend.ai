"""
Role Preset DTO v2 models for Manager API.
"""

from ai.backend.common.dto.manager.v2.role_preset.request import (
    BulkAddRolePermissionPresetsInput,
    BulkDeleteRolePresetsInput,
    BulkPurgeRolePresetsInput,
    BulkRemoveRolePermissionPresetsInput,
    BulkRestoreRolePresetsInput,
    CreateRolePresetInput,
    RolePresetFilter,
    RolePresetOrder,
    SearchRolePresetsInput,
    UpdateRolePresetInput,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    BulkAddRolePermissionPresetsPayload,
    BulkDeleteRolePresetsPayload,
    BulkPurgeRolePresetsPayload,
    BulkRemoveRolePermissionPresetsPayload,
    BulkRestoreRolePresetsPayload,
    BulkRolePermissionPresetFailureInfo,
    BulkRolePresetFailureInfo,
    CreateRolePresetPayload,
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
    "BulkAddRolePermissionPresetsInput",
    "BulkDeleteRolePresetsInput",
    "BulkPurgeRolePresetsInput",
    "BulkRemoveRolePermissionPresetsInput",
    "BulkRestoreRolePresetsInput",
    "CreateRolePresetInput",
    "RolePresetFilter",
    "RolePresetOrder",
    "SearchRolePresetsInput",
    "UpdateRolePresetInput",
    # Response DTOs
    "BulkAddRolePermissionPresetsPayload",
    "BulkDeleteRolePresetsPayload",
    "BulkPurgeRolePresetsPayload",
    "BulkRemoveRolePermissionPresetsPayload",
    "BulkRestoreRolePresetsPayload",
    "BulkRolePermissionPresetFailureInfo",
    "BulkRolePresetFailureInfo",
    "CreateRolePresetPayload",
    "RolePermissionPresetNode",
    "RolePresetNode",
    "SearchRolePresetsPayload",
    "UpdateRolePresetPayload",
)

"""
Role Permission Preset DTO v2 models for Manager API.
"""

from ai.backend.common.dto.manager.v2.role_permission_preset.request import (
    BulkAddRolePermissionPresetsInput,
    BulkRemoveRolePermissionPresetsInput,
    RolePermissionPresetFilter,
    RolePermissionPresetOrder,
    SearchRolePermissionPresetsInput,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.response import (
    BulkAddRolePermissionPresetsPayload,
    BulkRemoveRolePermissionPresetsPayload,
    BulkRolePermissionPresetFailureInfo,
    RolePermissionPresetNode,
    SearchRolePermissionPresetsPayload,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.types import (
    RolePermissionPresetEntry,
    RolePermissionPresetOrderField,
)

__all__ = (
    # Types
    "RolePermissionPresetEntry",
    "RolePermissionPresetOrderField",
    # Request DTOs
    "BulkAddRolePermissionPresetsInput",
    "BulkRemoveRolePermissionPresetsInput",
    "RolePermissionPresetFilter",
    "RolePermissionPresetOrder",
    "SearchRolePermissionPresetsInput",
    # Response DTOs
    "BulkAddRolePermissionPresetsPayload",
    "BulkRemoveRolePermissionPresetsPayload",
    "BulkRolePermissionPresetFailureInfo",
    "RolePermissionPresetNode",
    "SearchRolePermissionPresetsPayload",
)

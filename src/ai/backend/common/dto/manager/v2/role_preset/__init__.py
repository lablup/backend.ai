"""
Role Preset DTO v2 models for Manager API.
"""

from ai.backend.common.dto.manager.v2.role_preset.request import (
    BulkDeleteRolePresetsInput,
    BulkPurgeRolePresetsInput,
    BulkRestoreRolePresetsInput,
    CreateRolePresetInput,
    RolePresetFilter,
    RolePresetOrder,
    SearchRolePresetsInput,
    UpdateRolePresetInput,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    BulkDeleteRolePresetsPayload,
    BulkPurgeRolePresetsPayload,
    BulkRestoreRolePresetsPayload,
    BulkRolePresetFailureInfo,
    CreateRolePresetPayload,
    RolePresetNode,
    SearchRolePresetsPayload,
    UpdateRolePresetPayload,
)
from ai.backend.common.dto.manager.v2.role_preset.types import RolePresetOrderField

__all__ = (
    # Types
    "RolePresetOrderField",
    # Request DTOs
    "BulkDeleteRolePresetsInput",
    "BulkPurgeRolePresetsInput",
    "BulkRestoreRolePresetsInput",
    "CreateRolePresetInput",
    "RolePresetFilter",
    "RolePresetOrder",
    "SearchRolePresetsInput",
    "UpdateRolePresetInput",
    # Response DTOs
    "BulkDeleteRolePresetsPayload",
    "BulkPurgeRolePresetsPayload",
    "BulkRestoreRolePresetsPayload",
    "BulkRolePresetFailureInfo",
    "CreateRolePresetPayload",
    "RolePresetNode",
    "SearchRolePresetsPayload",
    "UpdateRolePresetPayload",
)

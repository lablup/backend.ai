"""
Role Preset DTO v2 models for Manager API.
"""

from ai.backend.common.dto.manager.v2.role_preset.request import (
    AddRolePresetPermissionsInput,
    CreateRolePresetInput,
    RemoveRolePresetPermissionsInput,
    RolePresetFilter,
    RolePresetOrder,
    SearchRolePresetsInput,
    UpdateRolePresetInput,
)
from ai.backend.common.dto.manager.v2.role_preset.response import (
    AddRolePresetPermissionsPayload,
    CreateRolePresetPayload,
    DeleteRolePresetPayload,
    RemoveRolePresetPermissionsPayload,
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
    RolePermissionPresetInfo,
    RolePresetOrderField,
)

__all__ = (
    # Types
    "EntityType",
    "OperationTypeDTO",
    "OrderDirection",
    "RBACElementTypeDTO",
    "RolePermissionPresetEntry",
    "RolePermissionPresetInfo",
    "RolePresetOrderField",
    # Request DTOs
    "AddRolePresetPermissionsInput",
    "CreateRolePresetInput",
    "RemoveRolePresetPermissionsInput",
    "RolePresetFilter",
    "RolePresetOrder",
    "SearchRolePresetsInput",
    "UpdateRolePresetInput",
    # Response DTOs
    "AddRolePresetPermissionsPayload",
    "CreateRolePresetPayload",
    "DeleteRolePresetPayload",
    "RemoveRolePresetPermissionsPayload",
    "RolePresetNode",
    "SearchRolePresetsPayload",
    "UpdateRolePresetPayload",
)

"""
RBAC DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.rbac.request import (
    AssignRoleInput,
    BulkAssignRoleInput,
    BulkRevokeRoleInput,
    CreatePermissionInput,
    CreateRoleInput,
    DeletePermissionInput,
    DeleteRoleInput,
    PurgeRoleInput,
    RevokeRoleInput,
    UpdatePermissionInput,
    UpdateRoleInput,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    CreateRolePayload,
    DeletePermissionPayload,
    DeleteRolePayload,
    PurgeRolePayload,
    RoleNode,
    UpdateRolePayload,
)
from ai.backend.common.dto.manager.v2.rbac.types import (
    EntityType,
    OperationType,
    OrderDirection,
    PermissionSummary,
    RoleOrderField,
    RoleSource,
    RoleStatus,
)

__all__ = (
    # Types
    "EntityType",
    "OperationType",
    "OrderDirection",
    "PermissionSummary",
    "RoleOrderField",
    "RoleSource",
    "RoleStatus",
    # Input models (request)
    "AssignRoleInput",
    "BulkAssignRoleInput",
    "BulkRevokeRoleInput",
    "CreatePermissionInput",
    "CreateRoleInput",
    "DeletePermissionInput",
    "DeleteRoleInput",
    "PurgeRoleInput",
    "RevokeRoleInput",
    "UpdatePermissionInput",
    "UpdateRoleInput",
    # Node and Payload models (response)
    "CreateRolePayload",
    "DeletePermissionPayload",
    "DeleteRolePayload",
    "PurgeRolePayload",
    "RoleNode",
    "UpdateRolePayload",
)

"""
RBAC DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.rbac.request import (
    CreateRoleInput,
    DeleteRoleInput,
    PurgeRoleInput,
    UpdateRoleInput,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    CreateRolePayload,
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
    "CreateRoleInput",
    "DeleteRoleInput",
    "PurgeRoleInput",
    "UpdateRoleInput",
    # Node and Payload models (response)
    "CreateRolePayload",
    "DeleteRolePayload",
    "PurgeRolePayload",
    "RoleNode",
    "UpdateRolePayload",
)

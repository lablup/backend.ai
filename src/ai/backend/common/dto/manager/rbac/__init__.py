"""
Common DTOs for RBAC system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    AssignedUserFilter,
    AssignedUserOrder,
    AssignRoleRequest,
    CreateRoleRequest,
    RevokeRoleRequest,
    RoleFilter,
    RoleOrder,
    SearchRolesRequest,
    SearchUsersAssignedToRoleRequest,
    StringFilter,
    UpdateRoleRequest,
)
from .response import (
    AssignedUserDTO,
    AssignRoleResponse,
    CreateRoleResponse,
    DeleteRoleResponse,
    GetRoleResponse,
    PaginationInfo,
    RevokeRoleResponse,
    RoleDTO,
    SearchRolesResponse,
    SearchUsersAssignedToRoleResponse,
    UpdateRoleResponse,
)
from .types import (
    AssignedUserOrderField,
    OrderDirection,
    RoleOrderField,
    RoleSource,
    RoleStatus,
)

__all__ = (
    # Types
    "RoleSource",
    "RoleStatus",
    "OrderDirection",
    "RoleOrderField",
    "AssignedUserOrderField",
    # Request DTOs
    "CreateRoleRequest",
    "UpdateRoleRequest",
    "AssignRoleRequest",
    "RevokeRoleRequest",
    "SearchRolesRequest",
    "SearchUsersAssignedToRoleRequest",
    "StringFilter",
    "RoleFilter",
    "RoleOrder",
    "AssignedUserFilter",
    "AssignedUserOrder",
    # Response DTOs
    "RoleDTO",
    "AssignedUserDTO",
    "CreateRoleResponse",
    "UpdateRoleResponse",
    "DeleteRoleResponse",
    "GetRoleResponse",
    "SearchRolesResponse",
    "AssignRoleResponse",
    "RevokeRoleResponse",
    "SearchUsersAssignedToRoleResponse",
    "PaginationInfo",
)

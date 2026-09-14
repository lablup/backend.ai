"""
RBAC DTOs for Manager API.
"""

from .path import (
    DeletePermissionPathParam,
    GetRolePathParam,
    SearchUsersAssignedToRolePathParam,
    UpdateRolePathParam,
)
from .request import (
    AssignedUserFilter,
    AssignedUserOrder,
    AssignRoleRequest,
    CreatePermissionRequest,
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
    CreatePermissionResponse,
    CreateRoleResponse,
    DeletePermissionResponse,
    DeleteRoleResponse,
    GetRoleResponse,
    PaginationInfo,
    PermissionDTO,
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
    # Path DTOs
    "GetRolePathParam",
    "UpdateRolePathParam",
    "SearchUsersAssignedToRolePathParam",
    "DeletePermissionPathParam",
    # Request DTOs
    "CreateRoleRequest",
    "UpdateRoleRequest",
    "AssignRoleRequest",
    "RevokeRoleRequest",
    "SearchRolesRequest",
    "SearchUsersAssignedToRoleRequest",
    "CreatePermissionRequest",
    "RoleFilter",
    "RoleOrder",
    "AssignedUserFilter",
    "AssignedUserOrder",
    "StringFilter",
    # Response DTOs
    "CreateRoleResponse",
    "GetRoleResponse",
    "UpdateRoleResponse",
    "DeleteRoleResponse",
    "SearchRolesResponse",
    "AssignRoleResponse",
    "RevokeRoleResponse",
    "SearchUsersAssignedToRoleResponse",
    "CreatePermissionResponse",
    "DeletePermissionResponse",
    "RoleDTO",
    "AssignedUserDTO",
    "PermissionDTO",
    "PaginationInfo",
    # Types
    "RoleSource",
    "RoleStatus",
    "OrderDirection",
    "RoleOrderField",
    "AssignedUserOrderField",
)

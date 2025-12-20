"""
RBAC DTOs for Manager API.
"""

from .path import (
    DeleteObjectPermissionPathParam,
    DeletePermissionPathParam,
    GetRolePathParam,
    SearchUsersAssignedToRolePathParam,
    UpdateRolePathParam,
)
from .request import (
    AssignedUserFilter,
    AssignedUserOrder,
    AssignRoleRequest,
    CreateObjectPermissionRequest,
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
    CreateObjectPermissionResponse,
    CreatePermissionResponse,
    CreateRoleResponse,
    DeleteObjectPermissionResponse,
    DeletePermissionResponse,
    DeleteRoleResponse,
    GetRoleResponse,
    ObjectPermissionDTO,
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
    "DeleteObjectPermissionPathParam",
    # Request DTOs
    "CreateRoleRequest",
    "UpdateRoleRequest",
    "AssignRoleRequest",
    "RevokeRoleRequest",
    "SearchRolesRequest",
    "SearchUsersAssignedToRoleRequest",
    "CreatePermissionRequest",
    "CreateObjectPermissionRequest",
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
    "CreateObjectPermissionResponse",
    "DeleteObjectPermissionResponse",
    "RoleDTO",
    "AssignedUserDTO",
    "PermissionDTO",
    "ObjectPermissionDTO",
    "PaginationInfo",
    # Types
    "RoleSource",
    "RoleStatus",
    "OrderDirection",
    "RoleOrderField",
    "AssignedUserOrderField",
)

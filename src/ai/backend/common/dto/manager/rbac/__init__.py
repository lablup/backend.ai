"""
RBAC DTOs for Manager API.
"""

from .path import (
    DeleteRolePathParam,
    GetRolePathParam,
    SearchUsersAssignedToRolePathParam,
    UpdateRolePathParam,
)
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
    # Path DTOs
    "GetRolePathParam",
    "UpdateRolePathParam",
    "DeleteRolePathParam",
    "SearchUsersAssignedToRolePathParam",
    # Request DTOs
    "CreateRoleRequest",
    "UpdateRoleRequest",
    "AssignRoleRequest",
    "RevokeRoleRequest",
    "SearchRolesRequest",
    "SearchUsersAssignedToRoleRequest",
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
    "RoleDTO",
    "AssignedUserDTO",
    "PaginationInfo",
    # Types
    "RoleSource",
    "RoleStatus",
    "OrderDirection",
    "RoleOrderField",
    "AssignedUserOrderField",
)

"""
Common DTOs for RBAC system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    RoleFilter,
    RoleOrder,
    SearchRolesRequest,
    StringFilter,
)
from .response import (
    GetRoleResponse,
    PaginationInfo,
    RoleDTO,
    SearchRolesResponse,
)
from .types import (
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
    # Request DTOs
    "SearchRolesRequest",
    "StringFilter",
    "RoleFilter",
    "RoleOrder",
    # Response DTOs
    "RoleDTO",
    "GetRoleResponse",
    "SearchRolesResponse",
    "PaginationInfo",
)

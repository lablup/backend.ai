"""
Common DTOs for user admin REST API used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    CreateUserRequest,
    DeleteUserRequest,
    PurgeUserRequest,
    SearchUsersRequest,
    UpdateUserRequest,
    UserFilter,
    UserOrder,
)
from .response import (
    CreateUserResponse,
    DeleteUserResponse,
    GetUserResponse,
    PaginationInfo,
    PurgeUserResponse,
    SearchUsersResponse,
    UpdateUserResponse,
    UserDTO,
)
from .types import (
    OrderDirection,
    UserOrderField,
    UserRole,
    UserStatus,
)

__all__ = (
    # Types
    "OrderDirection",
    "UserOrderField",
    "UserRole",
    "UserStatus",
    # Request DTOs
    "CreateUserRequest",
    "UpdateUserRequest",
    "SearchUsersRequest",
    "DeleteUserRequest",
    "PurgeUserRequest",
    "UserFilter",
    "UserOrder",
    # Response DTOs
    "UserDTO",
    "CreateUserResponse",
    "GetUserResponse",
    "SearchUsersResponse",
    "UpdateUserResponse",
    "DeleteUserResponse",
    "PurgeUserResponse",
    "PaginationInfo",
)

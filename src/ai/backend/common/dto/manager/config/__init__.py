"""
Common DTOs for config (dotfile) system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    CreateDomainDotfileRequest,
    CreateGroupDotfileRequest,
    CreateUserDotfileRequest,
    DeleteDomainDotfileRequest,
    DeleteGroupDotfileRequest,
    DeleteUserDotfileRequest,
    GetBootstrapScriptRequest,
    GetDomainDotfileRequest,
    GetGroupDotfileRequest,
    GetUserDotfileRequest,
    UpdateBootstrapScriptRequest,
    UpdateDomainDotfileRequest,
    UpdateGroupDotfileRequest,
    UpdateUserDotfileRequest,
)
from .response import (
    CreateDotfileResponse,
    DeleteDotfileResponse,
    DotfileItem,
    GetBootstrapScriptResponse,
    GetDotfileResponse,
    ListDotfilesResponse,
    UpdateBootstrapScriptResponse,
    UpdateDotfileResponse,
)
from .types import (
    MAXIMUM_DOTFILE_SIZE,
    DotfilePermission,
)

__all__ = (
    # Types
    "MAXIMUM_DOTFILE_SIZE",
    "DotfilePermission",
    # Request DTOs - User
    "CreateUserDotfileRequest",
    "GetUserDotfileRequest",
    "UpdateUserDotfileRequest",
    "DeleteUserDotfileRequest",
    "UpdateBootstrapScriptRequest",
    "GetBootstrapScriptRequest",
    # Request DTOs - Group
    "CreateGroupDotfileRequest",
    "GetGroupDotfileRequest",
    "UpdateGroupDotfileRequest",
    "DeleteGroupDotfileRequest",
    # Request DTOs - Domain
    "CreateDomainDotfileRequest",
    "GetDomainDotfileRequest",
    "UpdateDomainDotfileRequest",
    "DeleteDomainDotfileRequest",
    # Response DTOs
    "DotfileItem",
    "CreateDotfileResponse",
    "UpdateDotfileResponse",
    "DeleteDotfileResponse",
    "GetDotfileResponse",
    "ListDotfilesResponse",
    "GetBootstrapScriptResponse",
    "UpdateBootstrapScriptResponse",
)

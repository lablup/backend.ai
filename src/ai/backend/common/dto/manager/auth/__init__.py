"""
Common DTOs for auth system used by both Client SDK and Manager.
"""

from __future__ import annotations

from .request import (
    AuthorizeRequest,
    GetRoleRequest,
    SignoutRequest,
    SignupRequest,
    UpdateFullNameRequest,
    UpdatePasswordNoAuthRequest,
    UpdatePasswordRequest,
    UploadSSHKeypairRequest,
)
from .response import (
    AuthorizeResponse,
    GetRoleResponse,
    GetSSHKeypairResponse,
    SignoutResponse,
    SignupResponse,
    SSHKeypairResponse,
    UpdateFullNameResponse,
    UpdatePasswordNoAuthResponse,
    UpdatePasswordResponse,
)
from .types import (
    AuthResponse,
    AuthResponseType,
    AuthSuccessResponse,
    AuthTokenType,
    RequireTwoFactorAuthResponse,
    RequireTwoFactorRegistrationResponse,
    TwoFactorType,
    parse_auth_response,
)

__all__ = (
    # Types
    "AuthTokenType",
    "AuthResponseType",
    "TwoFactorType",
    "AuthResponse",
    "AuthSuccessResponse",
    "RequireTwoFactorRegistrationResponse",
    "RequireTwoFactorAuthResponse",
    "parse_auth_response",
    # Request DTOs
    "AuthorizeRequest",
    "GetRoleRequest",
    "SignupRequest",
    "SignoutRequest",
    "UpdateFullNameRequest",
    "UpdatePasswordRequest",
    "UpdatePasswordNoAuthRequest",
    "UploadSSHKeypairRequest",
    # Response DTOs
    "AuthorizeResponse",
    "GetRoleResponse",
    "SignupResponse",
    "SignoutResponse",
    "UpdateFullNameResponse",
    "UpdatePasswordResponse",
    "UpdatePasswordNoAuthResponse",
    "GetSSHKeypairResponse",
    "SSHKeypairResponse",
)

"""
Response DTOs for auth system.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import AuthSuccessResponse

__all__ = (
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


class AuthorizeResponse(BaseResponseModel):
    """Response for authorization."""

    data: AuthSuccessResponse = Field(description="Authorization result data")


class GetRoleResponse(BaseResponseModel):
    """Response for get role."""

    global_role: str = Field(description="Global role")
    domain_role: str = Field(description="Domain role")
    group_role: Optional[str] = Field(default=None, description="Group role")


class SignupResponse(BaseResponseModel):
    """Response for signup."""

    access_key: str = Field(description="Generated access key")
    secret_key: str = Field(description="Generated secret key")


class SignoutResponse(BaseResponseModel):
    """Response for signout (empty response)."""

    pass


class UpdateFullNameResponse(BaseResponseModel):
    """Response for update full name (empty response)."""

    pass


class UpdatePasswordResponse(BaseResponseModel):
    """Response for update password."""

    error_msg: Optional[str] = Field(default=None, description="Error message if failed")


class UpdatePasswordNoAuthResponse(BaseResponseModel):
    """Response for update password without auth."""

    password_changed_at: str = Field(description="Timestamp when password was changed (ISO 8601)")


class GetSSHKeypairResponse(BaseResponseModel):
    """Response for get SSH keypair (public key only)."""

    ssh_public_key: str = Field(description="SSH public key")


class SSHKeypairResponse(BaseResponseModel):
    """Response for generate/upload SSH keypair (both keys)."""

    ssh_public_key: str = Field(description="SSH public key")
    ssh_private_key: str = Field(description="SSH private key")

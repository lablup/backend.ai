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
    """Response for successful authorization."""

    data: AuthSuccessResponse = Field(
        description="Issued credentials (access_key/secret_key), user role, and account status",
    )


class GetRoleResponse(BaseResponseModel):
    """Response containing the user's roles at different scopes."""

    global_role: str = Field(description="System-wide role: 'superadmin' or 'user'")
    domain_role: str = Field(description="Domain-level role: 'admin' or 'user'")
    group_role: Optional[str] = Field(
        default=None,
        description="Group-level role if group ID was requested; None if not a member",
    )


class SignupResponse(BaseResponseModel):
    """Response for a successful signup with auto-generated API keypair."""

    access_key: str = Field(description="Auto-generated API access key")
    secret_key: str = Field(description="Auto-generated API secret key paired with access_key")


class SignoutResponse(BaseResponseModel):
    """Response for signout. Empty body; user and keypairs are now INACTIVE."""

    pass


class UpdateFullNameResponse(BaseResponseModel):
    """Response for update full name (empty response)."""

    pass


class UpdatePasswordResponse(BaseResponseModel):
    """Response for update password."""

    error_msg: Optional[str] = Field(
        default=None,
        description="Error detail on failure (e.g., new password mismatch); None on success",
    )


class UpdatePasswordNoAuthResponse(BaseResponseModel):
    """Response for updating an expired password without API auth."""

    password_changed_at: str = Field(
        description="ISO 8601 timestamp of when the password was changed",
    )


class GetSSHKeypairResponse(BaseResponseModel):
    """Response for retrieving the SSH keypair (public key only)."""

    ssh_public_key: str = Field(description="SSH public key associated with the access key")


class SSHKeypairResponse(BaseResponseModel):
    """Response for generate/upload SSH keypair (both keys returned)."""

    ssh_public_key: str = Field(description="SSH public key in standard format")
    ssh_private_key: str = Field(description="SSH private key in PEM format")

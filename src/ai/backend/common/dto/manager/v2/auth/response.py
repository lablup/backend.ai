"""
Response DTOs for auth DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.auth.types import (
    AuthCredentialInfo,
    PasswordChangeInfo,
    RoleInfo,
    SSHKeypairInfo,
)

__all__ = (
    "AuthorizePayload",
    "GetRolePayload",
    "GetSSHKeypairPayload",
    "SignoutPayload",
    "SignupPayload",
    "SSHKeypairPayload",
    "UpdateFullNamePayload",
    "UpdatePasswordNoAuthPayload",
    "UpdatePasswordPayload",
    "VerifyAuthPayload",
)


class AuthorizePayload(BaseResponseModel):
    """Payload for successful authorization containing issued credentials."""

    data: AuthCredentialInfo = Field(
        description="Issued credentials (access_key/secret_key), user role, and account status",
    )


class SignupPayload(BaseResponseModel):
    """Payload for a successful signup with auto-generated API keypair."""

    access_key: str = Field(description="Auto-generated API access key")
    secret_key: str = Field(description="Auto-generated API secret key paired with access_key")


class SignoutPayload(BaseResponseModel):
    """Payload for signout. Empty body; user and keypairs are now INACTIVE."""

    pass


class VerifyAuthPayload(BaseResponseModel):
    """Payload for auth verification. Echoes back the input to confirm credentials are valid."""

    authorized: str = Field(description="Authorization status string (always 'yes' when valid)")
    echo: str = Field(description="Echoed input string confirming the auth round-trip succeeded")


class GetRolePayload(BaseResponseModel):
    """Payload containing the user's roles at different scopes."""

    role: RoleInfo = Field(description="Multi-scope role information for the authenticated user")


class UpdateFullNamePayload(BaseResponseModel):
    """Payload for update full name (empty response)."""

    pass


class UpdatePasswordPayload(BaseResponseModel):
    """Payload for update password."""

    error_msg: str | None = Field(
        default=None,
        description="Error detail on failure (e.g., new password mismatch); None on success",
    )


class UpdatePasswordNoAuthPayload(BaseResponseModel):
    """Payload for updating an expired password without API auth."""

    password_change: PasswordChangeInfo = Field(
        description="Result of the password change operation including the change timestamp",
    )


class GetSSHKeypairPayload(BaseResponseModel):
    """Payload for retrieving the SSH keypair (public key only)."""

    ssh_public_key: str = Field(description="SSH public key associated with the access key")


class SSHKeypairPayload(BaseResponseModel):
    """Payload for generate/upload SSH keypair (both keys returned)."""

    keypair: SSHKeypairInfo = Field(description="Generated or uploaded SSH keypair data")

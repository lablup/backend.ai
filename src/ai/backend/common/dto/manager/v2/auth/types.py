"""
Common types for auth DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.auth.types import (
    AuthResponseType,
    AuthTokenType,
    TwoFactorType,
)

__all__ = (
    "AuthCredentialInfo",
    "AuthResponseType",
    "AuthTokenType",
    "PasswordChangeInfo",
    "RoleInfo",
    "SSHKeypairInfo",
    "TwoFactorInfo",
    "TwoFactorType",
)


class AuthCredentialInfo(BaseResponseModel):
    """Credential information returned after successful authorization."""

    access_key: str = Field(description="API access key issued to the user")
    secret_key: str = Field(description="API secret key paired with access_key")
    role: str = Field(description="User's system-wide role")
    status: str = Field(description="User account status")


class TwoFactorInfo(BaseResponseModel):
    """Two-factor authentication information."""

    type: TwoFactorType = Field(description="Type of 2FA method required")
    token: str = Field(description="Token required to complete 2FA registration or verification")


class RoleInfo(BaseResponseModel):
    """Multi-scope role information for the authenticated user."""

    global_role: str = Field(description="System-wide role: 'superadmin' or 'user'")
    domain_role: str = Field(description="Domain-level role: 'admin' or 'user'")
    group_role: str | None = Field(
        default=None,
        description="Group-level role if group ID was requested; None if not a member",
    )


class SSHKeypairInfo(BaseResponseModel):
    """SSH keypair data."""

    ssh_public_key: str = Field(description="SSH public key in standard format")
    ssh_private_key: str = Field(description="SSH private key in PEM format")


class PasswordChangeInfo(BaseResponseModel):
    """Result of a password change operation."""

    password_changed_at: str = Field(
        description="ISO 8601 timestamp of when the password was changed",
    )
